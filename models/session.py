import peewee as pw
from models.connection import ModelBase


class DBSession(ModelBase):
    uuid_session = pw.CharField()
    session_address = pw.CharField(null=True)
    ip_address = pw.CharField()
    dt_insert = pw.DateTimeField()
    dt_deadline = pw.DateTimeField()
