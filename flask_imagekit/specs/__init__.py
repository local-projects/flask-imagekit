import flask_imagekit.conf as conf
from copy import copy
from ..exceptions import MissingSource
from ..cachefiles.backends import get_default_cachefile_backend
from ..cachefiles.strategies import load_strategy
from ..utils import open_image, get_by_qname, process_image
from .. import hashers

class BaseImageSpec(object):
    """
    An object that defines how an new image should be generated from a source
    image.

    """

    cachefile_storage = None
    """A Django storage system to use to save a cache file."""

    cachefile_backend = None
    """
    An object responsible for managing the state of cache files. Defaults to
    an instance of ``IMAGEKIT_DEFAULT_CACHEFILE_BACKEND``

    """

    cachefile_strategy = conf.IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY
    """
    A dictionary containing callbacks that allow you to customize how and when
    the image file is created. Defaults to
    ``IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY``.

    """

    def __init__(self):
        self.cachefile_backend = self.cachefile_backend or get_default_cachefile_backend()
        self.cachefile_strategy = load_strategy(self.cachefile_strategy)

    def generate(self):
        raise NotImplementedError

    MissingSource = MissingSource
    """
    Raised when an operation requiring a source is attempted on a spec that has
    no source.

    """


class ImageSpec(BaseImageSpec):
    """
    An object that defines how to generate a new image from a source file using
    PIL-based processors. (See :mod:`imagekit.processors`)

    """

    processors = []
    """A list of processors to run on the original image."""

    format = None
    """
    The format of the output file. If not provided, ImageSpecField will try to
    guess the appropriate format based on the extension of the filename and the
    format of the input image.

    """

    options = None
    """
    A dictionary that will be passed to PIL's ``Image.save()`` method as keyword
    arguments. Valid options vary between formats, but some examples include
    ``quality``, ``optimize``, and ``progressive`` for JPEGs. See the PIL
    documentation for others.

    """

    autoconvert = True
    """
    Specifies whether automatic conversion using ``prepare_image()`` should be
    performed prior to saving.

    """

    def __init__(self, source):
        self.source = source
        super(ImageSpec, self).__init__()

    @property
    def cachefile_name(self):
        if not self.source:
            return None
        fn = get_by_qname(conf.IMAGEKIT_SPEC_CACHEFILE_NAMER, 'namer')
        return fn(self)

    @property
    def source(self):
        src = getattr(self, '_source', None)
        if not src:
            field_data = getattr(self, '_field_data', None)
            if field_data:
                src = self._source = getattr(field_data['instance'], field_data['attname'])
                del self._field_data
        return src

    @source.setter
    def source(self, value):
        self._source = value

    def __getstate__(self):
        state = copy(self.__dict__)
        return state

    def get_hash(self):
        return hashers.pickle([
            self.source.name,
            self.processors,
            self.format,
            self.options,
            self.autoconvert,
        ])

    def generate(self):
        if not self.source:
            raise MissingSource("The spec '%s' has no source file associated"
                                " with it." % self)

        # TODO: Move into a generator base class
        # TODO: Factor out a generate_image function so you can create a generator and only override the PIL.Image creating part. (The tricky part is how to deal with original_format since generator base class won't have one.)
        try:
            img = open_image(self.source)
        except ValueError:

            # Re-open the file -- https://code.djangoproject.com/ticket/13750
            self.source.open()
            img = open_image(self.source)

        return process_image(img, processors=self.processors,
                             format=self.format, autoconvert=self.autoconvert,
                             options=self.options)