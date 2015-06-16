from .specs import ImageSpec
from .registry import register, unregister


def initialize_imagekit(app, **kwargs):
    from .utils import set_flask_app, conf
    conf.set_configs(**kwargs)
    set_flask_app(app)

    from .template import generateimage
    app.add_template_global(generateimage)
