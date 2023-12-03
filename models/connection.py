import peewee as pw

from envs import MYSQL_EXTERNAL_PORT, MYSQL_HOST, MYSQL_ROOT_PASSWORD, MYSQL_DATABASE, MYSQL_INTERNAL_PORT

db = pw.MySQLDatabase(
    database=MYSQL_DATABASE,
    user="root",
    password=MYSQL_ROOT_PASSWORD,
    host=MYSQL_HOST,
    port=MYSQL_EXTERNAL_PORT,
    autocommit=False,
    autoconnect=False
)


SRC_TYPES = (('discord', 'discord'), ('telegram', 'telegram'))
TRADE_TYPES = (('market', 'Market'), ('limit', 'Limit'))
DIRECTION_TYPES = (('long', 'Long'), ('short', 'Short'))
STATUS = (
    ('idle', 'idle'),
    ('run', 'run'),
    ('stop', 'stop'),
    ('complete', 'complete')
)


class ModelBase(pw.Model):

    class Meta:
        database = db
