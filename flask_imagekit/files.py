from .django_ported.files import File

class BaseIKFile(File):
    """
    This class contains all of the methods we need from
    django.db.models.fields.files.FieldFile, but with the model stuff ripped
    out. It's only extended by one class, but we keep it separate for
    organizational reasons.

    """

    def __init__(self, storage):
        self.storage = storage

    def _require_file(self):
        if not self:
            raise ValueError()

    def _get_file(self):
        self._require_file()
        if not hasattr(self, '_file') or self._file is None:
            self._file = self.storage.open(self.name, 'rb')
        return self._file

    def _set_file(self, file):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    def _get_path(self):
        self._require_file()
        return self.storage.path(self.name)
    path = property(_get_path)

    def _get_url(self):
        self._require_file()
        return self.storage.url(self.name)
    url = property(_get_url)

    def _get_size(self):
        self._require_file()
        if not self._committed:
            return self.file.size
        return self.storage.size(self.name)
    size = property(_get_size)

    def open(self, mode='rb'):
        self._require_file()
        self.file.open(mode)

    def _get_closed(self):
        file = getattr(self, '_file', None)
        return file is None or file.closed
    closed = property(_get_closed)

    def close(self):
        file = getattr(self, '_file', None)
        if file is not None:
            file.close()