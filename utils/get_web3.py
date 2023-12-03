from web3 import Web3
from web3.middleware import geth_poa_middleware
from envs import RPC_URL


def get_web3():
    web3_ = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))
    web3_.middleware_onion.inject(geth_poa_middleware, layer=0)
    return web3_


if __name__ == '__main__':
    w = get_web3()
    print(w.isConnected())

    # // https://api.etherscan.io/api?module=account&action=txlist&address=0xddbd2b932c763ba5b1b7ae3b362eac3e8d40121a&startblock=0&endblock=99999999&page=1&offset=10&sort=asc&apikey=GYA2NNGXC57SE8BWMHNRQ1M4TB3BGR68VT
    # // https://api.etherscan.io/api?module=account&action=tokentx&contractaddress=0xdac17f958d2ee523a2206206994597c13d831ec7&address=0x618ffd1cdabee36ce5992a857cc7463f21272bd7&page=1&offset=100&startblock=0&endblock=27025780&sort=asc&apikey=GYA2NNGXC57SE8BWMHNRQ1M4TB3BGR68VT
    # // https://api.etherscan.io/api?module=account&action=txlistinternal&address=0x2c1ba59d6f58433fb1eaee7d20b26ed83bda51a3&startblock=0&endblock=2702578&page=1&offset=10&sort=asc&apikey=GYA2NNGXC57SE8BWMHNRQ1M4TB3BGR68VT
    #