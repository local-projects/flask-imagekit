import six
from ..utils import get_singleton

class JustInTime(object):
    """
    A strategy that ensures the file exists right before it's needed.

    """

    def on_existence_required(self, file):
        file.generate()

    def on_content_required(self, file):
        file.generate()


class DictStrategy(object):
    def __init__(self, callbacks):
        for k, v in callbacks.items():
            setattr(self, k, v)


def load_strategy(strategy):
    if isinstance(strategy, six.string_types):
        strategy = get_singleton(strategy, 'cache file strategy')
    elif isinstance(strategy, dict):
        strategy = DictStrategy(strategy)
    elif callable(strategy):
        strategy = strategy()
    return strategy
