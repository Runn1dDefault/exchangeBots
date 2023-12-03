import time

from orders_creator.make_orders import MakeOrders
from utils.create_tables import make_migrations


if __name__ == '__main__':
    make_migrations()
    print('Run make orders...')
    creator = MakeOrders()
    while True:
        creator.run()
        time.sleep(1)
