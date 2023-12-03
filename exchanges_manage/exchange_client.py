from typing import Union

from exchanges_manage.base_exchange_client import BaseExchangeClient
from exchanges_manage.exchanges.binance_order import Binance
from exchanges_manage.exchanges.bybit_order import Bybit
from exchanges_manage.exchanges.ftx_order import Ftx
from exchanges_manage.exchanges.okex_order import Okex


class ExchangeClient(BaseExchangeClient):
    def remove_all_active_orders(self, token: str) -> None:
        token = self.filter_token(token)
        if isinstance(self.exchange_client, Binance):
            self.exchange_client.close_active_orders(symbol=token)
        elif isinstance(self.exchange_client, Bybit):
            self.exchange_client.close_positions(symbol=token)
        # TODO: add for FTX and Okex classes logic here

    def delete_order(self, token: str, order_id: str) -> None:
        # TODO: needs tests for FTX and OKEX
        params = dict(order_id=order_id)
        if not isinstance(self.exchange_client, Ftx):
            params['symbol'] = token
        self.exchange_client.order_delete(**params)

    def open_position(self, token: str, side: str, order_type: str, leverage: int,
                      size: Union[float, int], stop_price: int = None) -> str:
        self.check_min_size(size)
        self.check_order_type(order_type, stop_price)

        token = self.filter_token(token)
        order_side = self.filter_order_side(side)
        params = dict(symbol=token, side=order_side, quantity=size, stop_price=stop_price,
                      order_type=order_type.lower())
        self.remove_all_active_orders(token=token)
        if isinstance(self.exchange_client, Binance):
            # TODO: raise Exceptions if position opened
            # pos_data = self.exchange_client.positions(symbol=token)
            # if pos_data and float(pos_data['positionAmt']) != .0:
            #     raise PositionError('Position already open', token)
            params['order_type'] = order_type.upper()
        elif isinstance(self.exchange_client, Bybit):
            assert isinstance(size, int)
            params['order_type'] = order_type.title()
        # TODO: add leverage get and leverage set methods for okex and ftx
        self.exchange_client.leverage_set(token, leverage=leverage)
        return self.get_order_id(self.exchange_client.order_create(**params))

    def stop_loss_order(self, token: str, side: str, order_type: str, size: Union[int, float],
                        stop_loss: float) -> str:
        self.check_min_size(size)
        token = self.filter_token(token)
        params = dict(symbol=token, side=self.filter_order_side(side), quantity=size, stop_price=stop_loss)
        func = self.exchange_client.order_create
        if isinstance(self.exchange_client, Binance):
            params['side'] = self.filter_order_side(side, turn_over=True)
            params['order_type'] = 'STOP_LIMIT' if order_type.lower() == 'limit' else 'STOP_MARKET'
            params['stop_price'] = int(stop_loss)
            params['closePosition'] = True
        elif isinstance(self.exchange_client, Bybit):
            params['order_type'] = order_type.title()
            params['stop_loss'] = int(params.pop('stop_price'))
        # TODO: needs tests for FTX and OKEX
        elif isinstance(self.exchange_client, Ftx):
            func = self.exchange_client.order_create_conditional
            params['order_type'] = "stop"
        elif isinstance(self.exchange_client, Okex):
            func = self.exchange_client.order_create_conditional
            params['is_take_profit'] = False
        return self.get_order_id(func(**params))

    def take_profit_order(self, token: str, side: str, order_type: str, size: Union[float, int],
                          take_profit: float, close_pos: bool = False) -> str:
        self.check_min_size(size)
        token = self.filter_token(token)
        params = dict(symbol=token, side=self.filter_order_side(side), quantity=size, stop_price=take_profit)
        func = self.exchange_client.order_create
        if isinstance(self.exchange_client, Binance):
            params['side'] = self.filter_order_side(side, turn_over=True)
            params['order_type'] = 'TAKE_PROFIT' if order_type.lower() == 'limit' else 'TAKE_PROFIT_MARKET'
            params['workingType'] = 'MARK_PRICE'
            params['stop_price'] = int(take_profit)
            params['closePosition'] = close_pos
        elif isinstance(self.exchange_client, Bybit):
            assert isinstance(size, int)
            params['order_type'] = order_type.title()
            params['take_profit'] = int(params.pop('stop_price'))
        # TODO: needs tests for FTX and OKEX
        elif isinstance(self.exchange_client, Ftx):
            func = self.exchange_client.order_create_conditional
            params['order_type'] = "takeProfit"
        elif isinstance(self.exchange_client, Okex):
            func = self.exchange_client.order_create_conditional
            params['is_take_profit'] = True

        return self.get_order_id(func(**params))

    def get_position(self, token: str) -> dict:
        data = dict()
        token = self.filter_token(token)
        positions_data = self.exchange_client.positions(token)
        if isinstance(self.exchange_client, Bybit):
            data['leverage'] = positions_data['leverage']
            data['symbol'] = positions_data['symbol']
            data['entry_price'] = positions_data['entry_price']
            data['stop_loss'] = positions_data['stop_loss']
            data['take_profit'] = positions_data['take_profit']
        elif isinstance(self.exchange_client, Binance):
            orders_list = self.exchange_client.order_list(symbol=token)
            if orders_list:
                for order in orders_list:
                    if order['closePosition'] and 'stop' in order['type'].lower():
                        data['stop_loss'] = order['stopPrice']
                    elif order['closePosition'] and 'take_profit' in order['type'].lower():
                        data['take_profit'] = order['stopPrice']
            data['leverage'] = positions_data['leverage']
            data['symbol'] = positions_data['symbol']
            data['entry_price'] = positions_data['entryPrice']
        # TODO: add for FTX and Okex classes logic here
        return data

    def get_order(self, token: str, order_id: Union[str, int]) -> dict:
        data = dict()
        token = self.filter_token(token)
        order_data = self.exchange_client.order_get(symbol=token, order_id=order_id)
        if isinstance(self.exchange_client, Binance):
            assert isinstance(order_id, int)
            if not order_data:
                orders_data = self.exchange_client.order_list()
                for o_data in orders_data:
                    if o_data.get('orderId') == order_id:
                        order_data = o_data
            if order_data:
                data['order_id'] = str(order_data['orderId'])
                data['order_type'] = order_data['origType']
                data['status'] = order_data['status']
                data['stop_price'] = float(order_data['stopPrice'])
        elif isinstance(self.exchange_client, Bybit):
            if order_data:
                data['order_id'] = order_data['order_id']
                data['order_type'] = order_data['order_type']
                data['status'] = order_data['order_status']
                data['stop_price'] = float(order_data['price'])
        # TODO: add for FTX and Okex classes logic here
        return data
