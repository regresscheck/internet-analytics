from datetime import timedelta
from requests_cache import CachedSession

session = CachedSession(
    'basic_cache',
    backend='filesystem',
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
