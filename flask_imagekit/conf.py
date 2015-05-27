
# TODO - MAKE TO WORK WITH FLASK CONFIG
IMAGEKIT_CACHEFILE_NAMER = 'flask_imagekit.cachefiles.namers.hash'
IMAGEKIT_SPEC_CACHEFILE_NAMER = 'flask_imagekit.cachefiles.namers.source_name_as_path'
IMAGEKIT_CACHEFILE_DIR = 'CACHE/images'
IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'flask_imagekit.cachefiles.backends.Simple'
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'flask_imagekit.cachefiles.strategies.JustInTime'

IMAGEKIT_DEFAULT_FILE_STORAGE = None

IMAGEKIT_CACHE_BACKEND = None
IMAGEKIT_CACHE_PREFIX = 'imagekit:'
IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY = True
