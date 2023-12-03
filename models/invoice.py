import peewee as pw
from models.connection import ModelBase


class DBEthInvoice(ModelBase):
    key = pw.CharField()
    address = pw.CharField()
    transaction_id = pw.CharField(null=True, default="")
    pending_transaction_id = pw.CharField(null=True, default="")
    amount = pw.CharField()
    currency = pw.CharField()
    dt_invoice_create = pw.DateTimeField()
    duration = pw.IntegerField()
