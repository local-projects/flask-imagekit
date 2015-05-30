from ...specs import SpecHost
from .utils import ImageSpecFileDescriptor
from ...registry import register

class SpecHostField(SpecHost):
    def _set_spec_id(self, cls, name):
        spec_id = getattr(self, 'spec_id', None)

        # Generate a spec_id to register the spec with. The default spec id is
        # "<app>:<model>_<field>"
        if not spec_id:
            spec_id = ('%s:%s' % (cls.__name__, name)).lower()

        # Register the spec with the id. This allows specs to be overridden
        # later, from outside of the model definition.
        super(SpecHostField, self).set_spec_id(spec_id)


class ImageSpecField(SpecHostField):
    """
    The heart and soul of the ImageKit library, ImageSpecField allows you to add
    variants of uploaded images to your models.

    """
    def __init__(self, processors=None, format=None, options=None,
            source=None, cachefile_storage=None, autoconvert=None,
            cachefile_backend=None, cachefile_strategy=None, spec=None,
            id=None, cls=None, name=None):

        SpecHost.__init__(self, processors=processors, format=format,
                options=options, cachefile_storage=cachefile_storage,
                autoconvert=autoconvert,
                cachefile_backend=cachefile_backend,
                cachefile_strategy=cachefile_strategy, spec=spec,
                spec_id=id)

        # TODO: Allow callable for source. See https://github.com/matthewwithanm/django-imagekit/issues/158#issuecomment-10921664
        self.source = source
        self.calling_ourselves = False

    def contribute_to_class(self, cls, name):
        def register_source_group(source):
            setattr(cls, name, ImageSpecFileDescriptor(self, name, source))
            self._set_spec_id(cls, name)

            # Add the model and field as a source for this spec id
            register.source_group(self.spec_id, ImageFieldSourceGroup(cls, source))

        if self.source:
            register_source_group(self.source)
        else:
            raise Exception("Must define a source")
