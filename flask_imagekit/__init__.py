def initialize_imagekit(admin, **kwargs):
    from .utils import set_flask_app, conf
    conf.set_configs(**kwargs)
    set_flask_app(admin.app)

    views = admin._views

    from .specs import ImageSpec
    from .registry import register, unregister
    for view in views:
        if hasattr(view, 'model'):
            attributes = dir(view.model)
            for attr in [nodash for nodash in attributes if not nodash.startswith('_')]:
                from .models import ImageSpecField
                try:
                    # Some model attributes may attempt to access a request object
                    # So we supply them with a dummy context to stop exceptions
                    with admin.app.test_request_context():
                        field = getattr(view.model, attr, None)

                        if isinstance(field, ImageSpecField):
                            field.contribute_to_class(view.model, attr)
                except:
                    pass