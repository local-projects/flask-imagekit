from ..utils import get_singleton, get_cache, sanitize_cache_key, get_flask_app, conf
from copy import copy


class CacheFileState(object):
    EXISTS = 'exists'
    GENERATING = 'generating'
    DOES_NOT_EXIST = 'does_not_exist'


def get_default_cachefile_backend():
    """
    Get the default file backend.

    """
    return get_singleton(conf.IMAGEKIT_DEFAULT_CACHEFILE_BACKEND,
                         'file backend')

class CachedFileBackend(object):
    existence_check_timeout = 5
    """
    The number of seconds to wait before rechecking to see if the file exists.
    If the image is found to exist, that information will be cached using the
    timeout specified in your CACHES setting (which should be very high).
    However, when the file does not exist, you probably want to check again
    in a relatively short amount of time. This attribute allows you to do that.

    """

    @property
    def cache(self):
        if not getattr(self, '_cache', None):
            self._cache = get_cache
        return self._cache

    def get_key(self, file):
        return sanitize_cache_key('%s%s-state' %
                                  (conf.IMAGEKIT_CACHE_PREFIX, file.name))

    def get_state(self, file, check_if_unknown=True):
        key = self.get_key(file)
        state = self.cache.get(key)
        if state is None and check_if_unknown:
            exists = self._exists(file)
            state = CacheFileState.EXISTS if exists else CacheFileState.DOES_NOT_EXIST
            self.set_state(file, state)
        return state

    def set_state(self, file, state):
        key = self.get_key(file)
        if state == CacheFileState.DOES_NOT_EXIST:
            self.cache.set(key, state, self.existence_check_timeout)
        else:
            self.cache.set(key, state)

    def __getstate__(self):
        state = copy(self.__dict__)
        # Don't include the cache when pickling. It'll be reconstituted based
        # on the settings.
        state.pop('_cache', None)
        return state

    def exists(self, file):
        return self.get_state(file) == CacheFileState.EXISTS

    def generate(self, file, force=False):
        raise NotImplementedError

    def generate_now(self, file, force=False):
        if force or self.get_state(file) not in (CacheFileState.GENERATING, CacheFileState.EXISTS):
            self.set_state(file, CacheFileState.GENERATING)
            try:
                file._generate()
                self.set_state(file, CacheFileState.EXISTS)
            except Exception as err:
                get_flask_app().logger.warning("Exception generating file, marking file as not existing: %s" % err)
                self.set_state(file, CacheFileState.DOES_NOT_EXIST)


class Simple(CachedFileBackend):
    """
    The most basic file backend. The storage is consulted to see if the file
    exists. Files are generated synchronously.

    """

    def generate(self, file, force=False):
        self.generate_now(file, force=force)

    def _exists(self, file):
        return bool(getattr(file, '_file', None)
                    or file.storage.exists(file.name))
