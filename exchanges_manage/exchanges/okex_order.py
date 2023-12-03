import base64
from datetime import datetime

from requests import Request, Session

from exchanges_manage.exchanges.base import BaseOrder
from exchanges_manage.exchanges.mixins import RequestSessionMixin


class Okex(BaseOrder, RequestSessionMixin):
    # https://www.okex.com/docs-v5/
    base_url_endpoint = 'https://www.okx.com'
    ORDER_TYPES = ('market', 'limit', 'post_only', 'fok', 'ioc', 'optimal_limit_ioc')

    def __init__(self, passphrase: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._passphrase = passphrase
        self.session = Session()

    def sign_request(self, request: Request) -> None:
        if self.api_key and self.api_secret and self._passphrase:
            ts = datetime.utcnow().isoformat()[:-3]+'Z'
            request.headers['OK-ACCESS-KEY'] = self.api_key
            request.headers['OK-ACCESS-SIGN'] = base64.b64encode(self.signature(ts, request).digest())
            request.headers['OK-ACCESS-TIMESTAMP'] = str(ts)
            request.headers['OK-ACCESS-PASSPHRASE'] = self._passphrase

    def balance(self, token: str = None):
        path = '/api/v5/account/balance'
        if token:
            balance_info = self.get(path, {'ccy': token})
            token_balance_info = [i for i in balance_info[0]['details'] if i['ccy'] == token]
            return token_balance_info[0] if len(token_balance_info) > 0 else balance_info
        return self.get(path)

    def order_delete(self, symbol: str, order_id: str):
        return self.post('/api/v5/trade/cancel-order', {"instId": symbol, "ordId": order_id})

    def order_update(self, order_id: str, size: str = None, price: str = None, close_on_fail: bool = False):
        params = {"cxlOnFail": close_on_fail, "ordId": order_id}
        if size is not None:
            params['newSz'] = size
        if price is not None:
            params['newPx'] = price
        return self.post('/api/v5/trade/amend-order', params)

    def order_get(self, order_id: str, symbol: str, **kwargs):
        # docs: all other parameters can be found here:
        # https://www.okex.com/docs-v5/en/#rest-api-trade-get-order-details
        return self.get('/api/v5/trade/order', {"instId": symbol, "ordId": order_id, **kwargs})

    def order_list(self, **kwargs):
        # docs: all other parameters can be found here:
        # https://www.okex.com/docs-v5/en/#rest-api-trade-get-order-list
        return self.get('/api/v5/trade/orders-pending', kwargs if kwargs else None)

    def order_create(self, symbol: str, side: str, quantity: float, order_type: str,
                     order_price: float = None, **kwargs):
        # docs: all other parameters can be found here:
        # https://www.okex.com/docs-v5/en/#rest-api-trade-place-order
        params = {
            "instId": symbol,
            "tdMode": 'cash',
            "side": side,
            "ordType": order_type,
            "sz": quantity,
            "px": order_price,
            **kwargs
        }
        return self.post('/api/v5/trade/order', params)

    def delete_all_open_orders(self, symbol: str):
        return self.post('/api/v5/trade/cancel-order', {"instId": symbol})

    def order_create_conditional(self, symbol: str, side: str, quantity: float,
                                 stop_price: float, is_take_profit: bool = False, order_price: int = 0,
                                 **kwargs):
        """
        order_price - If the price is -1, the order will be executed at the market price.
        """
        params = {
            "instId": symbol,
            "tdMode": "cash",
            "side": side,
            "ordType": "conditional",
            "sz": quantity,
            **kwargs
        }
        if stop_price and is_take_profit is False:
            params['slTriggerPx'] = str(stop_price)
            params['slOrdPx	'] = str(order_price)
        elif stop_price and is_take_profit:
            params['tpTriggerPx'] = str(stop_price)
            params['tpOrdPx	'] = str(order_price)
        return self.post('/api/v5/trade/order-algo', params)

    def symbol_info(self, symbol: str):
        data = self.get("/api/v5/market/ticker", {'instId': symbol})
        return data[0] if len(data) > 0 else None

    def symbols(self, instrument_type: str):
        return self.get('/api/v5/public/instruments', {'instType': instrument_type})
