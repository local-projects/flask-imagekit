import flask_imagekit.conf as conf
import re

# TODO - Does SimpleCache suffice?
from werkzeug.contrib.cache import SimpleCache
from hashlib import md5
from .exceptions import ImproperlyConfigured
from importlib import import_module
from pilkit.utils import *

bad_memcached_key_chars = re.compile('[\u0000-\u001f\\s]+')


def get_nonabstract_descendants(model):
    """ Returns all non-abstract descendants of the model. """
    if not model._meta.abstract:
        yield model
    for s in model.__subclasses__():
        for m in get_nonabstract_descendants(s):
            yield m


def get_by_qname(path, desc):
    try:
        dot = path.rindex('.')
    except ValueError:
        raise ImproperlyConfigured("%s isn't a %s module." % (path, desc))
    module, objname = path[:dot], path[dot + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing %s module %s: "%s"' %
                (desc, module, e))
    try:
        obj = getattr(mod, objname)
        return obj
    except AttributeError:
        raise ImproperlyConfigured('%s module "%s" does not define "%s"'
                % (desc[0].upper() + desc[1:], module, objname))


_singletons = {}


def get_singleton(class_path, desc):
    global _singletons
    cls = get_by_qname(class_path, desc)
    instance = _singletons.get(cls)
    if not instance:
        instance = _singletons[cls] = cls()
    return instance

# TODO: Not functionally required but should find a non django way to port
def autodiscover():
    pass

def call_strategy_method(file, method_name):
    strategy = getattr(file, 'cachefile_strategy', None)
    fn = getattr(strategy, method_name, None)
    if fn is not None:
        fn(file)


def sanitize_cache_key(key):
    if conf.IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY:
        # Memcached keys can't contain whitespace or control characters.
        new_key = bad_memcached_key_chars.sub('', key)

        # The also can't be > 250 chars long. Since we don't know what the
        # user's cache ``KEY_FUNCTION`` setting is like, we'll limit it to 200.
        if len(new_key) >= 200:
            new_key = '%s:%s' % (new_key[:200-33], md5(key).hexdigest())

        key = new_key
    return key

get_cache = SimpleCache()