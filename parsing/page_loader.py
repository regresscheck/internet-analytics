from datetime import timedelta

from matplotlib import backends
from requests_cache import CachedSession

session = CachedSession(
    '.http_cache',
    backend='sqlite',
    use_cache_dir=True,
    expire_after=timedelta(days=1)
)


class PageLoader():
    def __init__(self) -> None:
        # TODO: implement connection pool/proxies
        pass

    def get_url(self, url):
        response = session.get(url)
        # TODO: proper error/redirect handling
        assert response.status_code == 200
        return response.text
