import peewee as pw
from models.connection import ModelBase


class DBRate(ModelBase):
    coin = pw.CharField(unique=True)
    rate = pw.FloatField(default=0)
    contract_address = pw.CharField(default="")
    address = pw.CharField(default="")
    dt_updated = pw.DateTimeField(null=True)
