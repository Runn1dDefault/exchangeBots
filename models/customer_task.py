from datetime import datetime

import peewee as pw
from models import DBUser, Channel, Exchange
from models.connection import ModelBase, SRC_TYPES, STATUS


class CustomerTask(ModelBase):
    user = pw.ForeignKeyField(DBUser, on_delete='CASCADE', backref='tasks')
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', backref='customer_tasks')
    exchange = pw.ForeignKeyField(Exchange, on_delete='CASCADE', backref='customer_tasks')
    api_key = pw.CharField()
    api_secret = pw.CharField()
    api_passphrase = pw.CharField(null=True)
    api_reserve = pw.CharField(null=True)
    percent_portfolio = pw.IntegerField()  # TODO: change to float
    leverage = pw.BigIntegerField()
    status = pw.CharField(choices=STATUS, default="idle")
    updated_at = pw.DateTimeField(default=datetime.now())
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')
    update_order = pw.BooleanField(default=False)
    delete_order = pw.BooleanField(default=False)
