import datetime
import peewee as pw
from models.connection import ModelBase

STATUS = (
    ('idle', 'idle'),
    ('run', 'run'),
    ('stop', 'stop'),
    ('complete', 'complete')
)

SRC_TYPES = (('discord', 'discord'), ('telegram', 'telegram'))

ENTRY_TYPES = (('market', 'Market'), ('limit', 'Limit'))
DIRECTION_TYPES = (('long', 'Long'), ('short', 'Short'))


class ExchangeModel(ModelBase):
    name = pw.CharField(max_length=255)


class Channel(ModelBase):
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')
    channel_id = pw.CharField()
    name = pw.CharField(max_length=255)


class TraderTask(ModelBase):
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', on_update='CASCADE', backref='trader_tasks')
    entry = pw.CharField(choices=ENTRY_TYPES, default='market')
    token = pw.CharField()
    direction = pw.CharField(choices=DIRECTION_TYPES, default='long')
    stop_loss = pw.BigIntegerField()
    targets = pw.TextField()
    leverage = pw.BigIntegerField()
    status = pw.CharField(choices=STATUS, default="idle")
    updated_at = pw.DateTimeField(default=datetime.datetime.now())
    is_delete = pw.BooleanField(default=False)
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')


class CustomerTask(ModelBase):
    id = pw.PrimaryKeyField(null=False)
    user = ''  # TODO: add foreignkey to custom user
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', on_update='CASCADE', backref='customer_tasks')
    exchange = pw.ForeignKeyField(ExchangeModel, on_delete='CASCADE', on_update='CASCADE', backref='customer_tasks')
    api_key = pw.CharField()
    api_secret = pw.CharField()
    api_passphrase = pw.CharField(null=True)
    api_reserve = pw.CharField(null=True)
    percent_portfolio = pw.IntegerField()
    leverage = pw.BigIntegerField()
    status = pw.CharField(choices=STATUS, default="idle")
    updated_at = pw.DateTimeField(default=datetime.datetime.now())
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')


class Order(ModelBase):
    id = pw.PrimaryKeyField(null=False)
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', on_update='CASCADE', backref='orders')
    trader_task = pw.ForeignKeyField(TraderTask, on_delete='CASCADE', on_update='CASCADE', backref='orders')
    customer_task = pw.ForeignKeyField(CustomerTask, on_delete='CASCADE', on_update='CASCADE', backref='orders')
    exchange = pw.ForeignKeyField(ExchangeModel, on_delete='CASCADE', on_update='CASCADE', backref='customer_tasks')
    api_key = pw.CharField()
    api_secret = pw.CharField()
    api_passphrase = pw.CharField(null=True)
    api_reserve = pw.CharField(null=True)
    token = pw.CharField()
    entry = pw.CharField(choices=ENTRY_TYPES, default='market')
    direction = pw.CharField(choices=DIRECTION_TYPES, default='long')
    leverage = pw.BigIntegerField()
    percent_portfolio = pw.IntegerField()
    size = pw.CharField()
    stop_loss = pw.BigIntegerField()
    stop_loss_order_id = pw.CharField()
    stop_loss_is_active = pw.BooleanField(default=True)
    status = pw.CharField(choices=STATUS, default="idle")
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')


class TargetOrder(ModelBase):
    order = pw.ForeignKeyField(Order, field="id", on_delete='CASCADE', on_update='CASCADE', backref="targets")
    target = pw.BigIntegerField()
    is_active = pw.BooleanField(default=True)
    take_profit_order_id = pw.CharField()
