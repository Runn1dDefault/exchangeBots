from time import time
from typing import Optional, Dict, List

from requests import Request, Session

from exchanges_manage.exchanges.base import BaseOrder
from exchanges_manage.exchanges.mixins import RequestSessionMixin


class Ftx(BaseOrder, RequestSessionMixin):
    # https://docs.ftx.com/
    base_url_endpoint = 'https://ftx.com/api'

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.session = Session()

    def sign_request(self, request: Request) -> None:
        if self.api_key and self.api_secret:
            ts = int(time() * 1000)
            request.headers['FTX-KEY'] = self.api_key
            request.headers['FTX-SIGN'] = self.signature(ts, request).hexdigest()
            request.headers['FTX-TS'] = str(ts)

    def account(self) -> dict:
        return self.get(f'/account')

    def order_book(self, market: str, depth: int = None) -> dict:
        return self.get(f'/markets/{market}/orderbook', {'depth': depth})

    def order_list(self, market: str = None) -> List[dict]:
        # market -> symbol
        return self.get(f'/orders', {'market': market})

    def order_list_conditional(self, market: str = None) -> List[dict]:
        return self.get(f'/conditional_orders', {'market': market})

    def order_delete(self, order_id: str) -> dict:
        return self.delete(f'/orders/{order_id}')

    def delete_all_open_orders(self, symbol: str):
        return self.delete('/orders', {"market": symbol})

    def balance(self, token: str = None) -> List[dict]:
        wallet_balance_info = self.get('/wallet/balances')
        if token:
            token_balance_info = [i for i in wallet_balance_info if i['coin'] == token]
            return token_balance_info[0] if len(token_balance_info) > 0 else wallet_balance_info
        return wallet_balance_info

    def coins(self) -> List[dict]:
        return self.get('/wallet/coins')

    def symbol_info(self, symbol: str) -> Dict:
        return self.get('/markets/{symbol}'.format(symbol=symbol))

    def order_update(
            self, existing_order_id: Optional[str] = None, price: Optional[float] = None,
            size: Optional[float] = None, client_order_id: Optional[str] = None,
            **kwargs
    ) -> dict:
        path = f'/orders/{existing_order_id}/modify'
        return self.post(path, {
            **({'size': size} if size is not None else {}),
            **({'price': price} if price is not None else {}),
            **({'clientId': client_order_id} if client_order_id is not None else {}),
        })

    def order_create(self, symbol: str, side: str, price: float, quantity: float, type_: str = 'market',
                     reduce_only: bool = False, ioc: bool = False, post_only: bool = False,
                     client_id: str = None, reject_after_ts: float = None) -> dict:
        return self.post('/orders', {
            'market': symbol,
            'side': side,
            'price': price,
            'size': quantity,
            'type': type_.lower(),
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only,
            'clientId': client_id,
            'rejectAfterTs': reject_after_ts
        })

    def order_create_conditional(self, symbol: str, side: str, quantity: float, order_type: str,
                                 stop_loss: float = None, order_price: float = None,
                                 reduce_only: bool = False) -> dict:
        return self.post('/conditional_orders', {
            'market': symbol,
            'side': side,
            'triggerPrice': stop_loss,
            'size': quantity,
            'reduceOnly': reduce_only,
            'type': order_type,
            'orderPrice': order_price
        })

    def order_get(self, symbol: str, order_id: int):
        try:
            return self.get('/orders', {'market': symbol, 'id': order_id})['result']
        except Exception as e:
            print(e)
            pass

    def get_markets(self) -> List[dict]:
        return self.get('/markets')
