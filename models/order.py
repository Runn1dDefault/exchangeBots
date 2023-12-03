from typing import Union

import peewee as pw

from models.channel import Channel
from models.exchange import Exchange
from models.trader_task import TraderTask
from models.customer_task import CustomerTask
from models.connection import ModelBase, TRADE_TYPES, DIRECTION_TYPES, SRC_TYPES


class Order(ModelBase):
    id = pw.PrimaryKeyField(null=False)
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', backref='orders')
    trader_task = pw.ForeignKeyField(TraderTask, on_delete='CASCADE', backref='orders')
    customer_task = pw.ForeignKeyField(CustomerTask, on_delete='CASCADE', backref='orders')
    exchange = pw.ForeignKeyField(Exchange, on_delete='CASCADE', backref='orders')
    api_key = pw.CharField()
    api_secret = pw.CharField()
    api_passphrase = pw.CharField(null=True)
    api_reserve = pw.CharField(null=True)
    token = pw.CharField()
    trade_type = pw.CharField(choices=TRADE_TYPES, default='market')
    direction = pw.CharField(choices=DIRECTION_TYPES, default='long')
    leverage = pw.BigIntegerField()
    percent_portfolio = pw.IntegerField()   # TODO: change to float
    size = pw.CharField()
    stop_loss = pw.BigIntegerField()
    stop_loss_order_id = pw.CharField()
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')

    @classmethod
    def new_order(cls, customer_task: CustomerTask, trader_task: TraderTask, stop_loss_order_id: str,
                  size: Union[str, float]):
        return Order.create(channel_id=customer_task.channel_id, trader_task=trader_task, customer_task=customer_task,
                            exchange=customer_task.exchange, api_key=customer_task.api_key,
                            api_secret=customer_task.api_secret, direction=trader_task.direction,
                            api_passphrase=customer_task.api_passphrase, api_reserve=customer_task.api_reserve,
                            token=trader_task.token, trade_type=trader_task.trade_type,
                            leverage=customer_task.leverage, percent_portfolio=customer_task.percent_portfolio,
                            stop_loss=trader_task.stop_loss, stop_loss_order_id=stop_loss_order_id, size=str(size),
                            type_src=customer_task.type_src)


class TargetOrder(ModelBase):
    order = pw.ForeignKeyField(Order, on_delete='CASCADE', backref="targets")
    price = pw.BigIntegerField()
    take_profit_order_id = pw.CharField()
