from typing import Union

from exchanges_manage.exchanges.binance_order import Binance
from exchanges_manage.exchanges.bybit_order import Bybit
from exchanges_manage.exchanges.ftx_order import Ftx
from exchanges_manage.exchanges.okex_order import Okex
from exchanges_manage.exeptions import OrderTypeError, InvalidSize


class BaseExchangeClient:
    EXCHANGES = {'Binance': Binance, 'Okex': Okex, 'Ftx': Ftx, 'Bybit': Bybit}
    EXCHANGES_ORDER_ID_KEYS = {'Binance': 'orderId', 'Okex': 'ordId', 'Ftx': 'id', 'Bybit': 'order_id'}
    LAST_PRICE_KEYS = {'Binance': 'lastPrice', 'Okex': 'last', 'Ftx': 'last', 'Bybit': 'last_price'}

    def __init__(self, exchange_name: str, api_key: str = None, api_secret: str = None, passphrase: str = None,
                 is_testnet: bool = True):
        self.exchange_name = exchange_name.title()
        self._exchange_name_check(self.exchange_name)
        self.is_testnet = is_testnet
        self._api_key, self._api_secret, self._api_passphrase = api_key, api_secret, passphrase
        self.order_id_key = self.EXCHANGES_ORDER_ID_KEYS[self.exchange_name]
        self.last_price_key = self.LAST_PRICE_KEYS[self.exchange_name]

    def _exchange_name_check(self, exchange_name: str) -> None:
        if self.EXCHANGES.get(exchange_name) is None:
            raise ModuleNotFoundError('Not found exchange module for {}'.format(self.exchange_name))

    def filter_token(self, token: str):
        if 'usd' in token.lower():
            token = token.lower().replace('usdt', '').replace('usd', '').upper()
        if isinstance(self.exchange_client, Bybit):
            return token + 'USD'
        elif isinstance(self.exchange_client, Okex):
            return token + '-USDT'
        elif isinstance(self.exchange_client, Ftx):
            if 'perp' in token.lower():
                token.lower().replace('perp', '').upper()
            elif '0325' in token:
                return token + '-0325'
            return token + '-PERP'
        return token.upper() + 'USDT'

    @property
    def exchange_client(self):
        exchange_api_keys = {'api_key': self._api_key, 'api_secret': self._api_secret, 'is_testnet': self.is_testnet}
        if self._api_passphrase:
            exchange_api_keys['passphrase'] = self._api_passphrase
        return self.EXCHANGES[self.exchange_name](**exchange_api_keys)

    _base_side_buy, _base_side_sell = 'buy', 'sell'

    def filter_order_side(self, order_side: str, turn_over: bool = False) -> str:
        order_side = order_side.lower()
        assert order_side in ('long', 'short')
        check_to_direction = order_side == 'long' if turn_over is False else order_side != 'long'
        if isinstance(self.exchange_client, Binance):
            return self._base_side_buy.upper() if check_to_direction else self._base_side_sell.upper()
        elif isinstance(self.exchange_client, Bybit):
            return self._base_side_buy.title() if check_to_direction else self._base_side_sell.title()
        return self._base_side_buy.lower() if check_to_direction else self._base_side_sell.lower()

    @staticmethod
    def check_order_type(order_type: str, stop_price: int = None) -> None:
        order_type = order_type.lower()
        assert order_type in ('market', 'limit')
        if order_type == 'market' and stop_price is not None:
            raise OrderTypeError(order_type, 'stop_price can\'t not be send when order_type is: ')
        elif order_type == 'limit' and stop_price is None:
            raise OrderTypeError(order_type, 'stop_price can\'t not be None when order_type is: ')

    def get_order_id(self, order_data: dict):
        return order_data.get(self.order_id_key)

    def last_price(self, symbol: str) -> float:
        token = self.filter_token(symbol)
        symbol_info = self.exchange_client.symbol_info(symbol=token)
        return float(symbol_info[self.last_price_key])

    def calculate_qty(self, token: str, percentage: Union[int, float]) -> tuple:
        convert_type = float
        token = self.filter_token(token)
        usdt_balance_data = self.exchange_client.balance('USDT')
        if isinstance(self.exchange_client, Binance):
            usdt_balance = float(usdt_balance_data['availableBalance'])
        elif isinstance(self.exchange_client, Bybit):
            usdt_balance, convert_type = float(usdt_balance_data['USDT']['available_balance']), int
        elif isinstance(self.exchange_client, Okex):
            usdt_balance = float(usdt_balance_data['availEq'])
        else:
            usdt_balance = float(usdt_balance_data['total'])
        leverage = float(self.exchange_client.leverage(symbol=token))
        result_ = convert_type(((usdt_balance * percentage) / 100) * leverage)
        if result_ <= 0.0:
            raise ValueError({'percentage': f'Invalid param. Result less then zero or equal zero: {result_}'})
        return usdt_balance, result_

    def calc_token_first(self, symbol: str, usdt_balance: Union[float, int]) -> float:
        last_price = self.last_price(symbol)
        result = usdt_balance / last_price
        _, _decimals = str(result).split('.')
        return result if len(_decimals) <= 3 else round(result, 3)

    @staticmethod
    def check_min_size(size: Union[float, int]):
        if size < 0.001:
            raise InvalidSize('Less then minimum (0.001) :', size)
        _, decimals_ = str(float(size)).split('.')
        if len(decimals_) > 3:
            raise InvalidSize('Minimum length of decimals is 3. You send: ', size)
