import queue
import time

from peewee import JOIN, ModelSelect

from utils import run_thread
from exchanges_manage import ExchangeClient
from models import Order, TargetOrder, Exchange, TraderTask, CustomerTask, db


class MonitorOrders:
    _is_testnet: bool = True

    def __init__(self):
        self.queue_threads = queue.Queue(maxsize=self._max_threads)
        self.queue_tasks = queue.Queue(maxsize=15)

    @property
    def _max_threads(self) -> int:
        with db.atomic():
            return Exchange.select().count()

    @staticmethod
    def _update_customers_tasks_status(customers_tasks: ModelSelect, status: str) -> None:
        update_customers_tasks = []
        with db.atomic() as txn:
            try:
                for u_task in customers_tasks:
                    u_task.status = status
                    update_customers_tasks.append(u_task)
                if update_customers_tasks:
                    CustomerTask.bulk_update(update_customers_tasks, fields=[CustomerTask.status],
                                             batch_size=len(update_customers_tasks))
            except Exception as e:
                txn.rollback()
                print('Method "update_customers_tasks_status" :', e.args)
            else:
                txn.commit()

    @staticmethod
    def _remove_all_targets(order: Order, trader_task: TraderTask) -> None:
        c = 0
        while True:
            with db:
                all_targets = (TargetOrder.select().join(Order, JOIN.LEFT_OUTER)
                                                   .group_by(TargetOrder.id)
                                                   .where((Order.trader_task == trader_task) &
                                                          (Order.exchange == order.exchange)))

                for target in all_targets:
                    try:
                        exchange_client = ExchangeClient(exchange_name=order.exchange.name,
                                                         api_key=target.order.api_key,
                                                         api_secret=target.order.api_secret,
                                                         passphrase=target.order.api_passphrase)
                        exchange_client.remove_all_active_orders(token=target.order.token)
                    except:
                        continue
                    else:
                        c += 1

                print(f'Delete all orders of trader_tasks #{trader_task.id} on exchange {order.exchange.name}')
                if c == all_targets.count():
                    break

    @staticmethod
    def _new_stop_loss(order: Order, target: TargetOrder) -> None:
        print('New stop loss for order: ', order.id, ' Stop price: ', target.price)
        with db.atomic() as txn:
            try:
                exchange_client = ExchangeClient(exchange_name=order.exchange.name, api_key=order.api_key,
                                                 api_secret=order.api_secret, passphrase=order.api_passphrase)
                exchange_client.delete_order(order.token, order.stop_loss_order_id)
                new_sl_order_id = exchange_client.stop_loss_order(token=order.token, side=order.direction,
                                                                  order_type=order.trade_type,
                                                                  size=round(float(order.size), 3),
                                                                  stop_loss=target.price)
                order.stop_loss = target.price
                order.stop_loss_order_id = new_sl_order_id
                order.save()
                print(f'Deleted target #{target.id} Order ID: {target.take_profit_order_id}')
                target.delete_instance()
            except Exception as e:
                txn.rollback()
                print("Method 'new_stop_loss' :", e.args)
            else:
                txn.commit()

    def _delete_trader_task_orders(self, order: Order, trader_task: TraderTask) -> None:
        self._remove_all_targets(order, trader_task)
        with db.atomic() as txn:
            try:
                Order.delete().where((Order.trader_task == trader_task) &
                                     (Order.exchange == order.exchange)).execute()
            except Exception as e:
                txn.rollback()
                print('Method "delete_trader_task_orders" :', e.args)
            else:
                txn.commit()

    def _completed_trader_task(self, order: Order, status: str) -> None:
        with db:
            trader_task = TraderTask.get_by_id(order.trader_task.id)
            run_thread(order, trader_task, callback=self._delete_trader_task_orders, some_queue=self.queue_tasks,
                       max_size=self._max_threads)
            orders_count = trader_task.orders.count()
            if orders_count == 0:
                customers_tasks = (
                    CustomerTask.select().where((CustomerTask.exchange == order.exchange)
                                                & (CustomerTask.channel_id == trader_task.channel_id))
                )
                run_thread(customers_tasks, status, callback=self._update_customers_tasks_status,
                           some_queue=self.queue_tasks, max_size=self._max_threads)
                print(f'Trader task #{trader_task.id} completed on exchange {order.exchange.name}')

        with db.atomic() as txn:
            try:
                if orders_count == 0:
                    order.customer_task.status = status
                    order.customer_task.save()
                    trader_task.status = status
                    trader_task.save()
            except Exception as e:
                txn.rollback()
                print('Method "completed_trader_task" :', e.args)
            else:
                txn.commit()

    def __stop_loss(self, orders: ModelSelect, last_price: float) -> None:
        with db:
            print(f'Last Price {last_price} Long Stop loss orders: ', [i.id for i in orders])
            run_thread(orders, callback=self._checking_stop_loss,
                       some_queue=self.queue_tasks, max_size=self._max_threads)

    def _checking_stop_loss(self, orders: ModelSelect) -> None:
        for order in orders:
            with db:
                exchange_client = ExchangeClient(exchange_name=order.exchange.name, api_key=order.api_key,
                                                 api_secret=order.api_secret, passphrase=order.api_passphrase)
                order_id = int(order.stop_loss_order_id) \
                    if exchange_client.exchange_name == 'Binance' else order.stop_loss_order_id
                stop_loss_order = exchange_client.get_order(order.token, order_id=order_id)
                if not stop_loss_order:
                    run_thread(order, 'stop', callback=self._completed_trader_task, some_queue=self.queue_tasks,
                               max_size=self._max_threads)
                else:
                    # if the stop-loss did not work, you need to check the targets of the same order
                    run_thread(order, callback=self._checking_take_profits, some_queue=self.queue_tasks,
                               max_size=self._max_threads)

    def __take_profits(self, orders: ModelSelect, last_price: float) -> None:
        with db:
            print(f'Last Price {last_price} Short Take profits orders: ', [i.id for i in orders])
            run_thread(orders, callback=self._checking_take_profits, some_queue=self.queue_tasks,
                       max_size=self._max_threads)

    def _checking_take_profits(self, orders: ModelSelect) -> None:
        for order in orders:
            with db:
                exchange_client = ExchangeClient(exchange_name=order.exchange.name, api_key=order.api_key,
                                                 api_secret=order.api_secret, passphrase=order.api_passphrase)
                query = TargetOrder.select().where(TargetOrder.order == order)
                active_target = query.order_by(TargetOrder.price.asc()).first() \
                    if order.direction == 'long' else query.order_by(TargetOrder.price.desc()).first()

                order_id = int(active_target.take_profit_order_id) \
                    if exchange_client.exchange_name == 'Binance' else active_target.take_profit_order_id
                at_order_on_exchange = exchange_client.get_order(order.token, order_id=order_id)
                if not at_order_on_exchange:
                    run_thread(order, active_target, callback=self._new_stop_loss, some_queue=self.queue_tasks,
                               max_size=self._max_threads)
                    if order.targets.count() == 0:
                        run_thread(order, 'completed', callback=self._completed_trader_task,
                                   some_queue=self.queue_tasks, max_size=self._max_threads)

    def _checking_pair_orders_long(self, pair_orders, last_price: float) -> None:
        with db:
            orders_long = pair_orders.where(Order.direction == 'long')
            stop_loss_long = (orders_long.where(Order.stop_loss >= last_price)
                                         .order_by(Order.id).distinct())
            if stop_loss_long:
                self.__stop_loss(stop_loss_long, last_price)

            take_profits_long = (orders_long.join(TargetOrder, on=TargetOrder.order)
                                            .where(TargetOrder.order.not_in(stop_loss_long))
                                            .order_by(Order.id).distinct())
            if take_profits_long:
                self.__take_profits(take_profits_long, last_price)

    def _checking_pair_orders_short(self, pair_orders, last_price: float) -> None:
        with db:
            orders_short = pair_orders.where(Order.direction == 'short')
            stop_loss_short = (orders_short.where(Order.stop_loss <= last_price)
                                           .order_by(Order.id).distinct())          # orders
            if stop_loss_short:
                self.__stop_loss(stop_loss_short, last_price)

            take_profits_short = (orders_short.join(TargetOrder, on=TargetOrder.order)
                                              .where(TargetOrder.order.not_in(stop_loss_short))
                                              .order_by(Order.id).distinct())
            if take_profits_short:
                self.__take_profits(take_profits_short, last_price)

    def _quote_price(self, exchange: Exchange, pair: str) -> None:
        while True:
            with db:
                try:
                    exchange_client = ExchangeClient(exchange_name=exchange.name, is_testnet=self._is_testnet)
                    last_price = exchange_client.last_price(pair)
                except Exception as e:
                    print('Method "quote_price": ', e.args)
                    time.sleep(1)
                    continue
                else:
                    orders_query = Order.select().where((Order.exchange == exchange) & (Order.token == pair))
                    for func in (self._checking_pair_orders_long, self._checking_pair_orders_short):
                        run_thread(orders_query, last_price, callback=func, some_queue=self.queue_tasks,
                                   max_size=self._max_threads)

    def _group_pair(self, exchange: Exchange) -> None:
        with db:
            q = exchange.orders
            pairs = {i.token for i in q or []}
            for pair in pairs or []:
                run_thread(exchange, pair, callback=self._quote_price, some_queue=self.queue_tasks,
                           max_size=self._max_threads)

    def run(self) -> None:
        with db:
            for exchange in Exchange.select().order_by(Exchange.name.desc()).distinct():
                run_thread(exchange, callback=self._group_pair, some_queue=self.queue_threads,
                           max_size=self._max_threads)


if __name__ == '__main__':
    r = MonitorOrders()
    while True:
        r.run()
        time.sleep(1)
