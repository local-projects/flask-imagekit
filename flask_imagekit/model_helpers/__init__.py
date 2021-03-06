import os
from ..utils import conf


def get_local_fields(model, source_fields):
    """
    Get the model's local fields as a dict depending on the type of model
    library in use
    """
    local_fields = None

    # MONGOENGINE
    if hasattr(model, '_fields') and isinstance(model._fields, dict):
        local_fields = dict((field_name, field)
                            for field_name, field in model._fields.iteritems()
                            if field_name in source_fields)

    return local_fields


def get_image(field):
    """
    Get a file like object containing the content of the field's image
    """
    def handle_string(string):
        # The field might be a string representing the path to the image
        # or it may be an external url

        if string.startswith('http'):
            return get_http_asset(string)
        else:
            file_path = os.path.join(conf.MEDIA_ROOT, conf.BASE_PREFIX, string)
            if file_path.startswith('http'):
                return get_http_asset(file_path)
            file = open(file_path, 'rb')
            if file:
                return file
            else:
                raise Exception("Could not open a valid file for path: %s" % file_path)

    # Embedded documents should have a way of representing themselves in a way we can use
    # We offer them this ability through a method "to_imagekit"
    if hasattr(field, 'to_imagekit'):
        string = field.to_imagekit()
        return handle_string(string)
    elif hasattr(field, 'seek') and hasattr(field, 'read'):
        # The field itself can be treated as a file like object, just return it
        return field
    elif isinstance(field, basestring):
        return handle_string(field)

    raise Exception("Could not determine a way to extract data from the supplied field: %s" % field)


def get_http_asset(path):
    import requests
    import shutil
    from StringIO import StringIO

    file = StringIO()
    r = requests.get(path, stream=True)
    if r.status_code == 200:
        shutil.copyfileobj(r.raw, file)
        return file
    else:
        raise Exception("Http response: %s, trying to get file %s" % (r.status_code, path))
