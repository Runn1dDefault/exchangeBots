import time
from pprint import pprint

import requests
import typing as t
from datetime import datetime, timedelta

from web3 import Web3

from envs import API_ETHERSCAN_KEY
from models import create_tables, db, DBEthInvoice, DBEthTransaction, DBRate, DBUser

TIME_TO_WAIT: t.Union[int, float] = 5


def get_transactions(
        address: str,
        apikey: str,
        action: str,
        module: str = "account",
        startblock: int = 11912700,
        endblock: int = 99999999,
        page: int = 1,
        offset: int = 100,
        sort: str = "asc",
        contractaddress: str = "",
) -> list:
    headers = {
        'authority': 'api-ropsten.etherscan.io',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'cookie': '_gid=GA1.2.2109999008.1643283440; __stripe_mid=0081fb67-1d61-4ef4-aa14-d54bd7cb0c3a2fe1e9; __cf_bm=ps7lzxVOU3r_rvsfd9tHIXrn4tMYFtGR.MCRkDefj5s-1643355702-0-ASNOU3TkiXPWwer0U///qdRHOup8jKcHjnz0s4ABfVTPUoH+aQvFR5Pk7L1U5JN88n9JsyE/f1rEZZoGA0yuHKvyamDeH2p7CZMDdQdOixtz21EYgpZXL6qX5zWqEuoSzA==; __stripe_sid=db1503e4-51e0-4da6-b6d0-30bcdf3ddcdd2ee20a; amp_fef1e8=f30a1636-36fb-4684-9d86-a7cb0dde427bR...1fqfqh5gb.1fqfqh68u.1.1.2; _ga_0JZ9C3M56S=GS1.1.1643356133.1.1.1643356133.0; _ga=GA1.2.829697957.1638283438'
    }
    params = {
        "module": module,
        "action": action,
        "address": address,
        "startblock": startblock,
        "endblock": endblock,
        "page": page,
        "offset": offset,
        "sort": sort,
        "apikey": apikey,
    }
    if contractaddress:
        params["contractaddress"] = contractaddress
    try:
        response = requests.get("https://api.etherscan.io/api", headers=headers, params=params)
        # response = requests.get("https://api-ropsten.etherscan.io/api", params=params)
        # response = requests.request("GET", "https://api-ropsten.etherscan.io/api", headers=headers, params=params)
        # print(response.request.url)
        return response.json()["result"]
    except Exception as exs:
        print('ERROR.get transactions:', exs)
        return []


if __name__ == "__main__":
    while True:
        try:
            create_tables()
            break
        except Exception as e:
            print("Wait MySQL connection...", e)
            time.sleep(1)

    while True:

        try:
            with db:
                rates = list(DBRate.select())
        except Exception as ex:
            print('ERROR.get rates:', ex)
            coins = []

        for rate in rates:
            rate: DBRate

            time.sleep(10)
            if rate.coin == "usdt":
                continue

            new_transactions = get_transactions(address=rate.address,
                                                apikey=API_ETHERSCAN_KEY,
                                                contractaddress=rate.contract_address,
                                                action="txlist" if rate.coin == "eth" else "tokentx")

            if not new_transactions or (type(new_transactions) != list):
                continue

            for trx in new_transactions:

                try:
                    from_ = trx["from"].lower()
                    to_ = trx["to"].lower()
                    hash_ = trx["hash"].lower()
                    value_ = trx["value"]
                except:
                    continue

                if to_ != rate.address.lower():
                    continue

                try:
                    with db:
                        user: DBUser = DBUser.get_or_none(DBUser.address == from_)
                        existing_tx = DBEthTransaction.get_or_none(DBEthTransaction.transaction_id == hash_)
                        if existing_tx:
                            continue
                        known_invoices: DBEthInvoice = DBEthInvoice.get_or_none((DBEthInvoice.address == from_)
                                                                                & (DBEthInvoice.transaction_id == "")
                                                                                & (DBEthInvoice.pending_transaction_id == hash_)
                                                                                & (DBEthInvoice.amount == value_)
                                                                                & (DBEthInvoice.currency == rate.coin.lower()))
                        if not known_invoices:
                            DBEthTransaction.create(address=from_,
                                                    transaction_id=hash_,
                                                    transaction_dt=datetime.now(),
                                                    amount=value_,
                                                    currency=rate.coin.lower(),
                                                    suitable=False)
                            continue
                except Exception as ex:
                    print('ERROR.get existing_tx:', ex)
                    continue

                try:
                    print("------ TX ------------------------------------------------ >")
                    print(datetime.now(), from_, ":", Web3.fromWei(int(value_), "ether"), rate.coin)
                except:
                    pass

                try:
                    with db.atomic() as txn_db:
                        DBEthTransaction.create(address=from_,
                                                transaction_id=hash_,
                                                transaction_dt=datetime.now(),
                                                amount=value_,
                                                currency=rate.coin.lower(),
                                                suitable=True)

                        known_invoices.transaction_id = hash_
                        known_invoices.save()

                        if user.dt_end_subscription <= datetime.now():
                            user.dt_end_subscription = datetime.now() + timedelta(days=known_invoices.duration)
                        elif user.dt_end_subscription > datetime.now():
                            user.dt_end_subscription = user.dt_end_subscription + timedelta(days=known_invoices.duration)
                        user.save()

                        print("New dt_end_subscription:", user.dt_end_subscription)
                        print("------ TX END -------------------------------------------- >")

                except Exception as ext:
                    print('ERROR.write tx:', ext)
                    continue
