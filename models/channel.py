import peewee as pw

from models.connection import ModelBase, SRC_TYPES


class Channel(ModelBase):
    type_src = pw.CharField(choices=SRC_TYPES, default='discord')
    channel_id = pw.CharField()
    name = pw.CharField(max_length=255)
