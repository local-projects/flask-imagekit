import os
from .. import conf

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
    if hasattr(field, 'seek') and hasattr(field, 'read'):
        # The field itself can be treated as a file like object, just return it
        return field
    elif isinstance(field, basestring):
        # The field might be a string representing the path to the image
        file_path = os.path.join(conf.MEDIA_ROOT, field)
        file = open(file_path, 'rb')
        if file:
            return file
        else:
            raise Exception("Could not open a valid file for path: %s" % file_path)

    raise Exception("Could not determine a way to extract data from the supplied field: %s" % field)