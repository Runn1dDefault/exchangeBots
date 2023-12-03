import time

from models import create_tables


def make_migrations():
    while True:
        try:
            create_tables()
            break
        except Exception as e:
            print("Wait MySQL connection...", e)
            time.sleep(1)
