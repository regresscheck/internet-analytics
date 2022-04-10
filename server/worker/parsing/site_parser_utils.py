from urllib.parse import urlparse
from worker.parsing.sites.tjournal import TJournalParser
from worker.parsing.site_parser import SiteParser


_parsers = {}


def _register_parser(parser):
    assert issubclass(parser, SiteParser)
    domain = parser.get_supported_domain()
    assert domain not in _parsers
    _parsers[domain] = parser


_register_parser(TJournalParser)


def get_suitable_parser(driver):
    domain = urlparse(driver.current_url).netloc
    assert domain in _parsers

    parser_class = _parsers[domain]
    return parser_class(driver)
