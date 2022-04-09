from datetime import timedelta
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
        assert response.status_code in [200, 404]
        if not response.from_cache:
            # TODO: implement proper delay for uncached requests. Have unique timer for each domain
            time.sleep(2)
        return response.text
