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