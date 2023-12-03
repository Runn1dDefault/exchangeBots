import queue
import time
from typing import List

from peewee import JOIN

from utils import run_thread, waiting_threads
from exchanges_manage import ExchangeClient, Binance
from models import CustomerTask, Order, TargetOrder, TraderTask, db


class MakeOrders:
    _is_testnet: bool = True

    def __init__(self):
        self.max_size = 15
        self.tasks_queue = queue.Queue(maxsize=self.max_size)
        self.trader_queue = queue.Queue(maxsize=self.max_size)
        self.customer_queue = queue.Queue(maxsize=self.max_size)
        self.update_queue = queue.Queue(maxsize=self.max_size)
        self.creating_tasks = {}
        self.deleting_tasks = []

    def make_delete_orders(self, all_user_orders: List[Order], stop_trader_task: bool = False) -> None:
        with db:
            for order in all_user_orders:
                if order.customer_task not in self.deleting_tasks:
                    run_thread(order, stop_trader_task, callback=self._thread_delete_order,
                               some_queue=self.tasks_queue,
                               max_size=self.max_size)

    @staticmethod
    def _stop_all_trader_tasks(trader_task: TraderTask) -> bool:
        changed = False
        with db:

            orders = (Order.select().join(CustomerTask, JOIN.LEFT_OUTER)
                                    .group_by(Order.id)
                                    .where((Order.trader_task == trader_task) &
                                           (CustomerTask.status.in_(["idle", "run"]))))
            customers_tasks = (i.customer_task for i in orders)

        with db.atomic() as txn:
            try:
                trader_task.status = 'stop'
                trader_task.update_orders, trader_task.delete_orders = False, False
                for customer_task in customers_tasks:
                    customer_task.update_order, customer_task.delete_order = False, False
                    customer_task.status = 'stop'
                    customer_task.save()
                trader_task.save()
                changed = True
            except Exception as e:
                txn.rollback()
                changed = False
                print('Method "stop_all_trader_tasks": ', e.args)
            else:
                txn.commit()
            finally:
                return changed

    def make_update_orders(self, all_user_orders: List[Order]) -> None:
        tasks = {}
        with db:
            for order in all_user_orders:
                tasks[order.customer_task] = order.trader_task
                run_thread(order, callback=self._thread_delete_order, some_queue=self.update_queue,
                           max_size=self.max_size)

            waiting_threads(self.update_queue)
            for u_task, t_task in tasks.items():
                exchange_client = ExchangeClient(is_testnet=self._is_testnet, exchange_name=u_task.exchange.name,
                                                 api_key=u_task.api_key, api_secret=u_task.api_secret,
                                                 passphrase=u_task.api_passphrase)
                run_thread(exchange_client, t_task, u_task, True, callback=self._thread_create_order,
                           some_queue=self.tasks_queue, max_size=self.max_size)

    def _thread_delete_order(self, order: Order, stop_trader_task: bool = False) -> None:
        with db:
            u_task = order.customer_task
            self.deleting_tasks.append(u_task)
            order_exists = Order.select().where(Order.id == order.id).exists()

        with db.atomic() as txn:
            try:
                if order_exists:
                    exchange = ExchangeClient(exchange_name=order.exchange.name, api_key=order.api_key,
                                              api_secret=order.api_secret, passphrase=order.api_passphrase)
                    exchange.remove_all_active_orders(token=order.token)
                    if stop_trader_task:
                        while True:
                            stopped = self._stop_all_trader_tasks(order.trader_task)
                            if stopped:
                                break
                            continue

                    order.customer_task.status = 'stop'
                    order.customer_task.update_order, order.customer_task.delete_order = False, False
                    order.customer_task.save()
                    order.delete_instance()
                    time.sleep(0.1)

            except Exception as e:
                txn.rollback()
                print(f'Method "thread_delete_order" Order #{order.id}: ', e.args)
            else:
                txn.commit()
                self.deleting_tasks.remove(u_task)

    def create_orders(self, t_task: TraderTask, u_task: CustomerTask) -> None:
        with db:
            exchange_client = ExchangeClient(is_testnet=self._is_testnet, exchange_name=u_task.exchange.name,
                                             api_key=u_task.api_key, api_secret=u_task.api_secret,
                                             passphrase=u_task.api_passphrase)
            last_price = exchange_client.last_price(symbol=t_task.token)

            price_in_enry_range = t_task.entry_min <= last_price <= t_task.entry_max
            if self.creating_tasks.get(u_task) is None and price_in_enry_range:
                run_thread(exchange_client, t_task, u_task, True, callback=self._thread_create_order,
                           some_queue=self.tasks_queue, max_size=self.max_size)

    @staticmethod
    def create_orders_on_exchange(exchange_client: ExchangeClient, t_task: TraderTask,
                                  u_task: CustomerTask, open_pos: bool = True) -> dict:
        orders_data = dict(targets=[])
        with db.atomic():
            params = dict(token=t_task.token, side=t_task.direction, order_type=t_task.trade_type)

            _, size = exchange_client.calculate_qty(token=t_task.token, percentage=u_task.percent_portfolio)
            params['size'] = exchange_client.calc_token_first(params['token'], size) \
                if isinstance(exchange_client.exchange_client, Binance) else size
            orders_data['size'] = size

            if open_pos:
                exchange_client.open_position(**params, leverage=u_task.leverage, stop_price=None)
                print(f'Position opened on exchange: {exchange_client.exchange_name}')

            orders_data['stop_loss_order_id'] = exchange_client.stop_loss_order(**params, stop_loss=t_task.stop_loss)
            print(f"Create StopLoss order on {exchange_client.exchange_name}:", orders_data['stop_loss_order_id'])

            targets = [float(i) for i in t_task.targets.split(',') if i]
            min_or_max = max if exchange_client.filter_order_side(t_task.direction).lower() == 'buy' else min
            for target in targets:
                target_order_id = exchange_client.take_profit_order(
                    **params, take_profit=target, close_pos=True if min_or_max(targets) == target else False)
                orders_data['targets'].append((target_order_id, target))
                print(f"Create TakeProfit order on {exchange_client.exchange_name}:", target_order_id)
        return orders_data

    @staticmethod
    def _target_exists(order: Order, target_price: int) -> bool:
        with db.atomic():
            target_exists = TargetOrder.select().where((TargetOrder.price == target_price)
                                                       & (TargetOrder.order == order)).exists()
        return target_exists

    def _thread_create_order(self, exchange_client: ExchangeClient, t_task: TraderTask,
                             u_task: CustomerTask, open_pos: bool = True) -> None:
        with db:
            if Order.get_or_none((Order.trader_task == t_task) & (Order.customer_task == u_task)):
                print('Order already exists')
                return

        self.creating_tasks[u_task] = t_task

        with db.atomic() as txn:
            try:
                on_exchange_orders_data = self.create_orders_on_exchange(exchange_client, t_task, u_task, open_pos)
                order = Order.new_order(u_task, t_task,
                                        on_exchange_orders_data['stop_loss_order_id'],
                                        on_exchange_orders_data['size'])
                # after the commit, the status is updated,
                # so it makes no sense to put it in a separate atomic block down
                t_task.update_orders, t_task.delete_orders = False, False
                t_task.status = "run"
                t_task.save()
                u_task.update_order, u_task.delete_order = False, False
                u_task.status = "run"
                u_task.save()
            except Exception as e:
                txn.rollback()
                print('Method "thread_create_order" :', e.args)
            else:
                for target_tuple in on_exchange_orders_data['targets']:
                    target_order_id, target_price = target_tuple
                    if not self._target_exists(order, target_price):
                        with db.atomic() as target_txn:
                            try:
                                TargetOrder.create(price=target_price, order=order,
                                                   take_profit_order_id=target_order_id)
                            except Exception as e:
                                print(f'Method "thread_create_order" Order #{order.id} '
                                      f'Target price#{target_price}:', e.args)
                                target_txn.rollback()
                                txn.rollback()
                                exchange_client.remove_all_active_orders(token=order.token)
                                self.creating_tasks.pop(u_task)
                                return
                txn.commit()
            finally:
                self.creating_tasks.pop(u_task)

    def _make_order_from_trader(self, t_task: TraderTask, u_task: CustomerTask) -> None:
        with db:
            all_user_orders = Order.select().where((Order.trader_task == t_task)
                                                   & (Order.customer_task == u_task))
            if all_user_orders and t_task.delete_orders:
                print(f'Delete orders by trader task #{t_task.id}...')
                self.make_delete_orders(all_user_orders=all_user_orders, stop_trader_task=True)

            elif all_user_orders and t_task.update_orders:
                print(f'Update orders by trader task #{t_task.id}...')
                self.make_update_orders(all_user_orders=all_user_orders)

            elif not all_user_orders:
                self.create_orders(t_task=t_task, u_task=u_task)

    def _make_order_from_customer(self, t_task: TraderTask, u_task: CustomerTask) -> None:
        with db:
            all_user_orders = Order.select().where((Order.trader_task == t_task)
                                                   & (Order.customer_task == u_task))
            if not all_user_orders:
                self.create_orders(t_task=t_task, u_task=u_task)
            else:
                update_orders = (all_user_orders.join(CustomerTask, JOIN.LEFT_OUTER)
                                                .group_by(Order.id)
                                                .where(CustomerTask.update_order == True))
                if update_orders:
                    print(f'Update order by customer task #{u_task.id}...')
                    self.make_update_orders(all_user_orders=update_orders)

                delete_orders = (all_user_orders.join(CustomerTask, JOIN.LEFT_OUTER)
                                                .group_by(Order.id)
                                                .where(CustomerTask.delete_order == True))
                if delete_orders:
                    print(f'Delete order by customer task #{u_task.id}...')
                    self.make_delete_orders(all_user_orders=delete_orders)

    def run(self) -> None:
        with db:
            if self.trader_queue.empty():
                for t_task in TraderTask.select().where(TraderTask.status == "idle"):
                    for u_task in CustomerTask.select().where((CustomerTask.channel_id == t_task.channel_id)
                                                              & (CustomerTask.type_src == t_task.type_src)
                                                              & (CustomerTask.status.in_(["idle", "run"]))):
                        run_thread(t_task, u_task, callback=self._make_order_from_trader,
                                   some_queue=self.trader_queue, max_size=self.max_size)
                waiting_threads(self.trader_queue)

            if self.customer_queue.empty():
                for u_task in CustomerTask.select().where(CustomerTask.status == "idle"):
                    t_task = TraderTask.get_or_none((TraderTask.channel_id == u_task.channel_id)
                                                    & (TraderTask.type_src == u_task.type_src)
                                                    & (TraderTask.status.in_(["idle", "run"])))
                    if t_task:
                        run_thread(t_task, u_task, callback=self._make_order_from_customer,
                                   some_queue=self.customer_queue, max_size=self.max_size)
                waiting_threads(self.customer_queue)


if __name__ == '__main__':
    a = MakeOrders()
    while 1:
        a.run()
        time.sleep(1)
