import hmac
from typing import Optional, Dict, Any, Union

from requests import Request, Response


class RequestSessionMixin:
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request('GET', path, params=params)

    def post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request('POST', path, json=params)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request('DELETE', path, json=params)

    def request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, self.base_url + path, **kwargs)
        self.sign_request(request)
        response = self.session.send(request.prepare())
        return self.process_response(response)

    def signature(self, timestamp: Union[int, str], request: Request, url_path: str = None):
        prepared = request.prepare()
        url = prepared.path_url if url_path is None else url_path
        signature_payload = f'{timestamp}{prepared.method}{url}'
        if prepared.body:
            signature_payload += prepared.body
        return hmac.new(self.api_secret.encode(), signature_payload.encode(), 'sha256')

    @staticmethod
    def process_response(response: Response) -> Any:
        # TODO: implement the method individually in each class
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if data.get('data') is None and not data.get('success'):
                msg = data.get("error") if data.get("error") else data.get("msg")
                raise Exception(f'Status code: {response.status_code}\nError: {msg}')
            if data.get('result'):
                return data['result']
            if data.get('data') is not None:
                return data['data']
            return data
