from typing import Union


class OrderTypeError(Exception):
    def __init__(self, order_type: str, text):
        super().__init__(f'{text}: {order_type}')


class InvalidSize(Exception):
    def __init__(self, msg: str, size: Union[str, float, int]):
        self.size = size
        self.message = msg
        super().__init__(f'{msg} : {size}')


class PositionError(Exception):
    def __init__(self, msg: str, token: str):
        self.token = token
        self.message = msg
        super().__init__(f'{msg} \nFor token: {token}')
