from .registry import generator_registry
from .cachefiles import ImageCacheFile
from flask import Markup

def get_cachefile(generator_id, generator_kwargs, source=None):
    generator = generator_registry.get(generator_id, **generator_kwargs)
    return ImageCacheFile(generator)


class GenerateImage():
    def __init__(self, generator_id, html_attrs, generator_kwargs):
        self._generator_id = generator_id
        self._generator_kwargs = generator_kwargs
        self._html_attrs = html_attrs

        self.file = get_cachefile(self._generator_id,
                self._generator_kwargs)

    def __str__(self):
        attrs = self._html_attrs

        # Only add width and height if neither is specified (to allow for
        # proportional in-browser scaling).
        if not 'width' in attrs and not 'height' in attrs:
            attrs.update(width=self.file.width, height=self.file.height)

        attrs['src'] = self.file.url
        attr_str = ' '.join('%s="%s"' % (k, v) for k, v in
                attrs.items())
        return Markup('<img %s />' % attr_str)


def generateimage(generator_id, html_attrs={}, **generator_kwargs):
    """
    Creates an image based on the provided arguments.
    By default::
        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image %}
    generates an ``<img>`` tag::
        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" />
    You can add additional attributes to the tag using "--". For example,
    this::
        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image -- alt="Hello!" %}
    will result in the following markup::
        <img src="/path/to/34d944f200dd794bf1e6a7f37849f72b.jpg" width="100" height="100" alt="Hello!" />
    For more flexibility, ``generateimage`` also works as an assignment tag::
        {% generateimage 'myapp:thumbnail' source=mymodel.profile_image as th %}
        <img src="{{ th.url }}" width="{{ th.width }}" height="{{ th.height }}" />
    """
    return GenerateImage(generator_id, html_attrs, generator_kwargs)