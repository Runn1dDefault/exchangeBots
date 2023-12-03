import peewee as pw
from models.connection import ModelBase


class DBPrices(ModelBase):
    duration = pw.IntegerField()
    price = pw.IntegerField()
    month = pw.IntegerField()
