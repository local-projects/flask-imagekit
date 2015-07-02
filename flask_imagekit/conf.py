class Conf():

    def set_configs(self, **kwargs):
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs.pop(key))

    # TODO - MAKE TO WORK WITH FLASK CONFIG
    MEDIA_ROOT = '/tmp/flask-imagekit/'
    MEDIA_URL = '/static/'
    FILE_UPLOAD_PERMISSIONS = None
    FILE_UPLOAD_DIRECTORY_PERMISSIONS = None

    S3_KEY = None
    S3_SECRET = None
    S3_BUCKET = None

    BASE_PREFIX = ''

    IMAGEKIT_CACHEFILE_NAMER = 'flask_imagekit.cachefiles.namers.hash'
    IMAGEKIT_SPEC_CACHEFILE_NAMER = 'flask_imagekit.cachefiles.namers.source_name_as_path'
    IMAGEKIT_CACHEFILE_DIR = 'CACHE/images'
    IMAGEKIT_DEFAULT_CACHEFILE_BACKEND = 'flask_imagekit.cachefiles.backends.Simple'
    IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'flask_imagekit.cachefiles.strategies.JustInTime'

    IMAGEKIT_DEFAULT_FILE_STORAGE = 'flask_imagekit.django_ported.storage.FileSystemStorage'

    IMAGEKIT_CACHE_BACKEND = None
    IMAGEKIT_CACHE_PREFIX = 'imagekit:'
    IMAGEKIT_USE_MEMCACHED_SAFE_CACHE_KEY = False
