from time import time


class BaseOrder:
    base_url_endpoint: str = None
    test_url_endpoint: str = None

    def __init__(self, api_key: str = None, api_secret: str = None, is_testnet: bool = False, **kwargs):
        self.api_key = api_key
        self.api_secret = api_secret
        if is_testnet and self.test_url_endpoint is None:
            raise AttributeError('For a test network, you need to specify the attribute test_url_endpoint!')
        self.base_url = self.base_url_endpoint if is_testnet is False else self.test_url_endpoint

    def balance(self, *args, **kwargs):
        pass

    def symbol_info(self, *args, **kwargs):
        pass

    def order_book(self, symbol: str):
        pass

    def order_get(self, *args, **kwargs):
        """Method for getting order"""
        pass

    def order_list(self, *args, **kwargs):
        """Method for getting orders list"""
        pass

    def order_create(self, *args, **kwargs):
        """Method for creating order"""
        pass

    def order_delete(self, *args, **kwargs):
        """Method for deleting order"""
        pass

    def order_update(self, *args, **kwargs):
        """Method for order updating"""
        pass

    @staticmethod
    def get_timestamp() -> int:
        return int(time() * 1000)
