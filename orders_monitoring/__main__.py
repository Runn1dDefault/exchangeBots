import time

from orders_monitoring import MonitorOrders
from utils.create_tables import make_migrations

if __name__ == '__main__':
    make_migrations()
    print('Run monitoring orders...')
    monitor = MonitorOrders()
    while True:
        monitor.run()
        time.sleep(1)
