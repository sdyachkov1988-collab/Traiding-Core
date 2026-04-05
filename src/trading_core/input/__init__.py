"""Input and context foundation seams."""

from trading_core.input.context import SimpleMarketContextAssembler
from trading_core.input.models import RawMarketEvent
from trading_core.input.normalizers import DictEventNormalizer

__all__ = [
    "DictEventNormalizer",
    "RawMarketEvent",
    "SimpleMarketContextAssembler",
]
