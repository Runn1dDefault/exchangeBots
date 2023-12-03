import peewee as pw
from models.connection import ModelBase


class DBEthTransaction(ModelBase):
    address = pw.CharField()
    transaction_id = pw.CharField()
    transaction_dt = pw.DateTimeField()
    amount = pw.CharField()
    currency = pw.CharField()
    suitable = pw.BooleanField()
