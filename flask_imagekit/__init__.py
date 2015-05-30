from .specs import ImageSpec
from .registry import register, unregister

def initialize_imagekit(admin):
    views = admin._views
    for view in views:
        if hasattr(view, 'model'):
            attributes = dir(view.model)
            for attr in [nodash for nodash in attributes if not nodash.startswith('_')]:
                from .models import ImageSpecField
                field = getattr(view.model, attr, None)
                if isinstance(field, ImageSpecField):
                    field.contribute_to_class(view.model, attr)