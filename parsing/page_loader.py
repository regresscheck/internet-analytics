import requests


class PageLoader():
    def __init__(self) -> None:
        # TODO: implement connection pool/proxies
        pass

    def get_url(self, url):
        # TODO: cache results somewhere
        response = requests.get(url)
        # TODO: proper error/redirect handling
        assert response.status_code == 200
        return response.text
