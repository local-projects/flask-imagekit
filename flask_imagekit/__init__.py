from .specs import ImageSpec
from .registry import register, unregister


def initialize_imagekit(admin, **kwargs):
    from .utils import set_flask_app, conf
    conf.set_configs(**kwargs)
    set_flask_app(admin.app)

    from .template import generateimage
    admin.app.add_template_global(generateimage)

    views = admin._views

    # Some model attributes may attempt to access a request object
    # So we supply them with a dummy context to stop exceptions
    with admin.app.test_request_context():
        from .models import ImageSpecField

        for view in views:
                if hasattr(view, 'model'):
                    attributes = dir(view.model)
                    for attr in [nodash for nodash in attributes if not nodash.startswith('_')]:
                        field = getattr(view.model, attr, None)

                        if isinstance(field, ImageSpecField):
                            field.contribute_to_class(view.model, attr)
