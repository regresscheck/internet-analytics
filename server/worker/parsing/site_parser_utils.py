from urllib.parse import urlparse
from worker.parsing.sites.pikabu import PikabuParser
from worker.parsing.sites.tjournal import TJournalParser
from worker.parsing.site_parser import SiteParser


_parsers = {}


class NoSuitableParserException(Exception):
    def __init__(self, url, domain):
        self.url = url
        self.domain = domain

    def __str__(self):
        return f"No suitable parser for domain '{self.domain}' from URL '{self.url}'"


def _register_parser(parser):
    assert issubclass(parser, SiteParser)
    domain = parser.get_supported_domain()
    assert domain not in _parsers
    _parsers[domain] = parser


_register_parser(TJournalParser)
_register_parser(PikabuParser)


def get_suitable_parser(driver):
    domain = urlparse(driver.current_url).netloc
    if domain not in _parsers:
        raise NoSuitableParserException(driver.current_url, domain)

    parser_class = _parsers[domain]
    return parser_class(driver)
