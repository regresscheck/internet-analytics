from datetime import timedelta

from matplotlib import backends
from requests_cache import CachedSession
import time

session = CachedSession(
    '.http_cache',
    backend='sqlite',
    use_cache_dir=True,
    expire_after=timedelta(days=7)
)


class PageLoader():
    def __init__(self) -> None:
        # TODO: implement connection pool/proxies
        pass

    def get_url(self, url, params={}):
        response = session.get(url, params=params)
        # TODO: proper error/redirect handling
        assert response.status_code == 200
        if not response.from_cache:
            # TODO: implement proper delay for uncached requests
            time.sleep(1)
        return response.text
