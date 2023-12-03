from datetime import datetime
from pprint import pprint
from typing import List, Union

from binance.error import ClientError
from binance.futures import Futures

from exchanges_manage.exchanges.base import BaseOrder


class Binance(BaseOrder):
    # docs: https://binance-docs.github.io/apidocs/futures/en/
    test_url_endpoint = 'https://testnet.binancefuture.com'
    _order_path = '/fapi/v1/order'
    ORDER_TYPES = ('LIMIT', 'MARKET', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET',
                   'TRAILING_STOP_MARKET')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = Futures(key=self.api_key, secret=self.api_secret, base_url=self.base_url)

    @property
    def recv_window(self):
        for i in (3000, 4000, 5000, 6000, 7000, 10000, 15000):
            timestamp = int(datetime.now().timestamp() * 1000)
            serverTime = self.get_server_timestamp(i)
            if timestamp < (serverTime + 1000) and (serverTime - timestamp) <= i:
                return i

    def get_server_timestamp(self, recv_win: int) -> int:
        return self.session.sign_request('GET', '/fapi/v1/time', {'recvWindow': recv_win})['serverTime']

    def balance(self, token: str = None, **kwargs) -> List[dict]:
        wallet_balance_data = self.session.balance(**kwargs)
        if token:
            token_balance_info = [i for i in wallet_balance_data if i['asset'] == token]
            return token_balance_info[0] if len(token_balance_info) > 0 else wallet_balance_data
        return wallet_balance_data

    def account(self, **kwargs) -> dict:
        kwargs['recvWindow'] = self.recv_window
        return self.session.account(**kwargs)

    def order_get(self, symbol: str, order_id: int, **kwargs) -> dict:
        kwargs['recvWindow'] = self.recv_window
        try:
            return self.session.query_order(symbol=symbol, orderId=order_id, **kwargs)
        except ClientError as e:
            pass
            # TODO: warning
            # print('Warning: ', e)

    def order_list(self, symbol: str = None) -> List[dict]:
        return self.session.get_orders(symbol=symbol, recvWindow=self.recv_window)

    def order_create(self, symbol: str, side: str,
                     order_type: str,  quantity: float, stop_price: int = None, **kwargs) -> dict:
        kwargs['recvWindow'] = self.recv_window
        return self.session.new_order(symbol=symbol, stopPrice=stop_price, quantity=quantity,
                                      side=side, type=order_type, **kwargs)

    def last_price(self, symbol: str) -> float:
        symbol_info = self.symbol_info(symbol=symbol)
        return float(symbol_info['lastPrice'])

    def delete_all_open_orders(self, symbol: str):
        return self.session.cancel_open_orders(symbol=symbol, recvWindow=self.recv_window)

    def order_delete(self, symbol: str, order_id: Union[str, int], **kwargs) -> bool:
        order = self.session.sign_request(
            'DELETE', self._order_path,
            {'symbol': symbol, 'orderId': int(order_id), 'timestamp': self.get_timestamp(),
             'recvWindow': self.recv_window})
        if order.get('status') == 'CANCELED':
            return True
        return False

    def order_update(self, symbol: str, order_id: int, **update_params) -> dict:
        delete_keys = ('status', 'clientOrderId', 'orderId', 'updateTime',
                       'avgPrice', 'origQty', 'cumQty', 'executedQty', 'origType')
        change_keys = {'origQty': 'quantity', 'origType': 'type', 'avgPrice': 'activationPrice'}
        order = self.order_delete(symbol=symbol, order_id=order_id)
        for key, value in order.items():
            if key not in delete_keys and key not in update_params.keys():
                setattr(update_params, key, value)
            if key in change_keys.keys():
                setattr(update_params, change_keys[key], value)
        return self.order_create(**update_params)

    def order_book(self, symbol: str) -> dict:
        return self.session.book_ticker(symbol)

    def symbol_info(self, symbol: str) -> Union[dict, List[dict]]:
        return self.session.ticker_24hr_price_change(symbol=symbol)

    def leverage_set(self, symbol: str, leverage: int, margin_type: str = 'CROSSED'):
        assert 1 <= leverage <= 125
        self.change_margin_type(symbol, margin_type)
        return self.session.change_leverage(symbol=symbol, leverage=leverage, recvWindow=self.recv_window)

    def leverage(self, symbol: str = None):
        return self.positions(symbol)['leverage']

    def positions(self, symbol: str = None):
        positions = self.account()['positions']
        if symbol is None:
            return positions

        for i in positions:
            if i.get('symbol') == symbol:
                return i

    def close_active_orders(self, symbol: str, **kwargs):
        return self.session.cancel_open_orders(symbol=symbol, **kwargs)

    def change_margin_type(self, symbol: str, margin_type: str = 'CROSSED'):
        try:
            return self.session.change_margin_type(symbol=symbol, marginType=margin_type)
        except ClientError as e:
            if e.status_code != 400 or e.error_message != 'No need to change margin type.':
                raise e
