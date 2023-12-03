from datetime import datetime

import peewee as pw

from models.channel import Channel
from models.connection import ModelBase, TRADE_TYPES, DIRECTION_TYPES, SRC_TYPES, STATUS


class TraderTask(ModelBase):
    channel_id = pw.ForeignKeyField(Channel, on_delete='CASCADE', backref='trader_tasks')
    trade_type = pw.CharField(choices=TRADE_TYPES, default='market')
    token = pw.CharField()
    direction = pw.CharField(choices=DIRECTION_TYPES, default='long')
    entry_min = pw.FloatField()
    entry_max = pw.FloatField()
    stop_loss = pw.BigIntegerField()
    targets = pw.TextField()  # INFO: Хранить через запятую
    leverage = pw.BigIntegerField()
    status = pw.CharField(choices=STATUS, default="idle")
    updated_at = pw.DateTimeField(default=datetime.now())
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')
    delete_orders = pw.BooleanField(default=False)
    update_orders = pw.BooleanField(default=False)
