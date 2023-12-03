from datetime import datetime, timedelta

from models.connection import db
from models.session import DBSession
from models.user import DBUser
from models.transaction import DBEthTransaction
from models.invoice import DBEthInvoice
from models.rate import DBRate
from models.prices import DBPrices
from models.exchange import Exchange
from models.channel import Channel
from models.trader_task import TraderTask
from models.customer_task import CustomerTask
from models.order import Order, TargetOrder


def create_tables():
    with db:
        DBUser.create_table()
        DBSession.create_table()
        DBEthTransaction.create_table()
        DBEthInvoice.create_table()
        DBRate.create_table()
        DBPrices.create_table()
        Exchange.create_table()
        Channel.create_table()
        TraderTask.create_table()
        CustomerTask.create_table()
        Order.create_table()
        TargetOrder.create_table()

        try:
            DBUser.create(id=1,
                          address="0x163203863Fb7A6871aBaFf2a52D7106800d504C9",
                          status="admin",
                          dt_end_subscription=datetime.now() + timedelta(days=9999),
                          dt_joined_day=datetime.now())
        except:
            pass

        try:
            DBUser.create(id=2,
                          address="0x52B9A87554d4E5D5770fb1a7BC642CdC5B2CdD1a",
                          status="admin",
                          dt_end_subscription=datetime.now() + timedelta(days=9999),
                          dt_joined_day=datetime.now())
        except:
            pass

        try:
            DBRate.create(
                id=1,
                coin="eth",
                rate=1,
                address="0x163203863Fb7A6871aBaFf2a52D7106800d504C9"
            )
        except:
            pass
        try:
            DBRate.create(
                id=2,
                coin="usdt",
                rate=1,
                contract_address="0xdac17f958d2ee523a2206206994597c13d831ec7",
                address="0x163203863Fb7A6871aBaFf2a52D7106800d504C9",
            )
        except:
            pass

        # try:
        #     DBRate.create(
        #         id=3,
        #         coin="jpg",
        #         rate=1,
        #         contract_address="0x64Df298BADE5722d399A6A781BE883CeD57DbC2C",
        #         address="0x163203863Fb7A6871aBaFf2a52D7106800d504C9",
        #     )
        # except:
        #     pass

        try:
            DBPrices.create(id=1, duration=30, price=40, month=1)
        except:
            pass
        try:
            DBPrices.create(id=2, duration=90, price=100, month=3)
        except:
            pass
        try:
            DBPrices.create(id=3, duration=180, price=180, month=6)
        except:
            pass
        try:
            DBPrices.create(id=4, duration=360, price=350, month=12)
        except:
            pass
