import peewee as pw
from models.connection import ModelBase


class Exchange(ModelBase):
    name = pw.CharField(max_length=255, unique=True)
