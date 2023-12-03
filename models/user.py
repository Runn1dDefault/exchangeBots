import peewee as pw
from models.connection import ModelBase


class DBUser(ModelBase):
    address = pw.CharField()
    status = pw.CharField()
    dt_end_subscription = pw.DateTimeField()
    dt_joined_day = pw.DateTimeField()

    discord_name = pw.CharField(null=True, default="")
    discord_id = pw.CharField(null=True, default="")
    discord_role = pw.CharField(default="none")
