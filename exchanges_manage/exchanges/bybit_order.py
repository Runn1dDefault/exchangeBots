import functools
from typing import Union, List

from pybit import HTTP

from exchanges_manage.exchanges.base import BaseOrder


def search_result_key(func):
    @functools.wraps(func)
    def return_result(self, *args, **kwargs) -> Union[dict, List[dict]]:
        data = func(self, *args, **kwargs)
        if type(data) is dict and data and data.get('result'):
            return data['result']
        return data

    return return_result


class Bybit(BaseOrder):
    # docs: https://bybit-exchange.github.io/docs/inverse/
    test_url_endpoint = 'https://api-testnet.bybit.com'
    ORDER_TYPES = ('Limit', 'Market')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = HTTP(api_key=self.api_key, api_secret=self.api_secret, endpoint=self.base_url)

    def leverage(self, symbol: str):
        return self.positions(symbol=symbol)['leverage']

    @search_result_key
    def leverage_set(self, symbol: str, leverage: int):
        if int(self.leverage(symbol=symbol)) != leverage:
            return self.session.set_leverage(symbol=symbol, leverage=leverage)

    @search_result_key
    def balance(self, symbol: str, **kwargs):
        return self.session.get_wallet_balance(coin=symbol, **kwargs)

    @search_result_key
    def positions(self, symbol: str = None):
        return self.session.my_position(symbol=symbol)

    @search_result_key
    def order_get(self, symbol: str, order_id: str):
        try:
            return self.session.query_active_order(symbol=symbol, order_id=order_id)
        except Exception as e:
            print(e)

    @search_result_key
    def order_get_conditional(self, symbol: str, order_id: str):
        try:
            return self.session.get_conditional_order(symbol=symbol, stop_order_id=order_id)
        except Exception as e:
            print(e)

    @search_result_key
    def order_list(self, symbol: str):
        return self.session.get_active_order(symbol=symbol)

    @search_result_key
    def order_book(self, symbol: str):
        return self.session.orderbook(symbol=symbol)

    @search_result_key
    def order_create(self, symbol: str, side: str, order_type: str, quantity: int, stop_price: int = None,
                     take_profit: int = None, stop_loss: int = None, **kwargs):
        return self.session.place_active_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            qty=quantity,
            time_in_force='GoodTillCancel',
            price=stop_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            **kwargs
        )

    @search_result_key
    def order_update(self, symbol: str, order_id: str, p_r_qty: int, p_r_price: int, **update_params):
        """
        /
        :param p_r_qty: New order quantity. Required for modifications
        :param p_r_price: New order price.  Required for modifications
        """
        return self.session.replace_active_order(
            symbol=symbol,
            order_id=order_id,
            p_r_qty=p_r_qty,
            p_r_price=p_r_price,
            **update_params
        )

    @search_result_key
    def order_delete(self, symbol: str, order_id: str):
        return self.session.cancel_active_order(symbol=symbol, order_id=order_id)

    def delete_all_open_orders(self, symbol: str):
        return self.session.cancel_all_active_orders(symbol=symbol)

    def symbol_info(self, symbol: str):
        return self.session.latest_information_for_symbol(symbol=symbol)['result'][0]

    @search_result_key
    def close_positions(self, symbol: str):
        return self.session.close_position(symbol=symbol)
