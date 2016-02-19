import errno
import os
import locks
import shutil
from StringIO import StringIO
from datetime import datetime
from inspect import getargspec
from urlparse import urljoin
from .files import File
from .utils import get_valid_filename, get_random_string, filepath_to_uri
from ..utils import conf
from ..exceptions import SuspiciousFileOperation

__all__ = ('Storage', 'FileSystemStorage')

class Storage(object):
    """
    A base storage class, providing some default behaviors that all other
    storage systems can inherit or override, as necessary.
    """

    # The following methods represent a public interface to private methods.
    # These shouldn't be overridden by subclasses unless absolutely necessary.

    def open(self, name, mode='rb'):
        """
        Retrieves the specified file from storage.
        """
        return self._open(name, mode)

    def save(self, name, content, max_length=None):
        """
        Saves new content to the file specified by name. The content should be
        a proper File object or any python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name

        if not hasattr(content, 'chunks'):
            content = File(content)

        args, varargs, varkw, defaults = getargspec(self.get_available_name)
        if 'max_length' in args:
            name = self.get_available_name(name, max_length=max_length)
        else:
            name = self.get_available_name(name)

        name = self._save(name, content)

        # Store filenames with forward slashes, even on Windows
        return str(name.replace('\\', '/'))

    # These methods are part of the public API, with default implementations.

    def get_valid_name(self, name):
        """
        Returns a filename, based on the provided filename, that's suitable for
        use in the target storage system.
        """
        return get_valid_filename(name)

    def get_available_name(self, name, max_length=None):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        # If the filename already exists, add an underscore and a random 7
        # character alphanumeric string (before the file extension, if one
        # exists) to the filename until the generated filename doesn't exist.
        # Truncate original name if required, so the new filename does not
        # exceed the max_length.
        while self.exists(name) or (max_length and len(name) > max_length):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
            if max_length is None:
                continue
            # Truncate file_root if max_length exceeded.
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                # Entire file_root was truncated in attempt to find an available filename.
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage can not find an available filename for "%s". '
                        'Please make sure that the corresponding file field '
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))
        return name

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """
        raise NotImplementedError("This backend doesn't support absolute paths.")

    # The following methods form the public API for storage systems, but with
    # no default implementations. Subclasses must implement *all* of these.

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        raise NotImplementedError('subclasses of Storage must provide a delete() method')

    def exists(self, name):
        """
        Returns True if a file referenced by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        raise NotImplementedError('subclasses of Storage must provide an exists() method')

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.
        """
        raise NotImplementedError('subclasses of Storage must provide a listdir() method')

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        raise NotImplementedError('subclasses of Storage must provide a size() method')

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a Web browser.
        """
        raise NotImplementedError('subclasses of Storage must provide a url() method')

    def accessed_time(self, name):
        """
        Returns the last accessed time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError('subclasses of Storage must provide an accessed_time() method')

    def created_time(self, name):
        """
        Returns the creation time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError('subclasses of Storage must provide a created_time() method')

    def modified_time(self, name):
        """
        Returns the last modified time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError('subclasses of Storage must provide a modified_time() method')


class FileSystemStorage(Storage):
    """
    Standard filesystem storage
    """

    def __init__(self, location=None, base_url=None, file_permissions_mode=None,
            directory_permissions_mode=None):
        if location is None:
            location = conf.MEDIA_ROOT
        self.base_location = location
        self.location = os.path.abspath(self.base_location)
        if base_url is None:
            base_url = conf.MEDIA_URL
        elif not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        self.file_permissions_mode = (
            file_permissions_mode if file_permissions_mode is not None
            else conf.FILE_UPLOAD_PERMISSIONS
        )
        self.directory_permissions_mode = (
            directory_permissions_mode if directory_permissions_mode is not None
            else conf.FILE_UPLOAD_DIRECTORY_PERMISSIONS
        )

    def _open(self, name, mode='rb'):
        return File(open(self.path(name), mode))

    def _save(self, name, content):
        full_path = self.path(name)

        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            try:
                if self.directory_permissions_mode is not None:
                    # os.makedirs applies the global umask, so we reset it,
                    # for consistency with file_permissions_mode behavior.
                    old_umask = os.umask(0)
                    try:
                        os.makedirs(directory, self.directory_permissions_mode)
                    finally:
                        os.umask(old_umask)
                else:
                    os.makedirs(directory)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(directory):
            raise IOError("%s exists and is not a directory." % directory)

        # There's a potential race condition between get_available_name and
        # saving the file; it's possible that two threads might return the
        # same name, at which point all sorts of fun happens. So we need to
        # try to create the file, but if it already exists we have to go back
        # to get_available_name() and try again.

        while True:
            try:
                # This file has a file path that we can move.
                if hasattr(content, 'temporary_file_path'):
                    shutil.move(content.temporary_file_path(), full_path)

                # This is a normal uploadedfile that we can stream.
                else:
                    # This fun binary flag incantation makes os.open throw an
                    # OSError if the file already exists before we open it.
                    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             getattr(os, 'O_BINARY', 0))
                    # The current umask value is masked out by os.open!
                    fd = os.open(full_path, flags, 0o666)
                    _file = None
                    try:
                        locks.lock(fd, locks.LOCK_EX)
                        for chunk in content.chunks():
                            if _file is None:
                                mode = 'wb' if isinstance(chunk, bytes) else 'wt'
                                _file = os.fdopen(fd, mode)
                            _file.write(chunk)
                    finally:
                        locks.unlock(fd)
                        if _file is not None:
                            _file.close()
                        else:
                            os.close(fd)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # Ooops, the file exists. We need a new file name.
                    name = self.get_available_name(name)
                    full_path = self.path(name)
                else:
                    raise
            else:
                # OK, the file save worked. Break out of the loop.
                break

        if self.file_permissions_mode is not None:
            os.chmod(full_path, self.file_permissions_mode)

        return name

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        name = self.path(name)
        # If the file exists, delete it from the filesystem.
        # Note that there is a race between os.path.exists and os.remove:
        # if os.remove fails with ENOENT, the file was removed
        # concurrently, and we can continue normally.
        if os.path.exists(name):
            try:
                os.remove(name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    def exists(self, name):
        return os.path.exists(self.path(name))

    def listdir(self, path):
        path = self.path(path)
        directories, files = [], []
        for entry in os.listdir(path):
            if os.path.isdir(os.path.join(path, entry)):
                directories.append(entry)
            else:
                files.append(entry)
        return directories, files

    def path(self, name):
        return os.path.join(self.location, name)

    def size(self, name):
        return os.path.getsize(self.path(name))

    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urljoin(self.base_url, filepath_to_uri(name))

    def accessed_time(self, name):
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))


class S3Storage(Storage):
    """
    Amazon Simple Storage Service using Boto

    This storage backend supports opening files in read or write
    mode and supports streaming(buffering) data in chunks to S3
    when writing.

    This is based on iserko's "django-storages"
    (https://github.com/iserko/django-storages/blob/master/storages/backends/s3boto.py)
    Modified to work with flask_imagekit
    """
    def __init__(self, location=None, base_url=None, **kwargs):
        if location is None:
            location = conf.MEDIA_ROOT
        self.location = location
        if base_url is None:
            base_url = conf.MEDIA_URL
        elif not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url

        self.s3_key = conf.S3_KEY
        self.s3_secret = conf.S3_SECRET
        self.s3_bucket = conf.S3_BUCKET

        self.prefix = conf.BASE_PREFIX

        self._entries = {}
        self._bucket = None
        self._connection = None

    @property
    def connection(self):
        import boto
        if self._connection is None:
            self._connection = boto.connect_s3(self.s3_key, self.s3_secret)

        return self._connection

    @property
    def bucket(self):
        """
        Get the current bucket. If there is no current bucket object
        create it.
        """
        if self._bucket is None:
            self._bucket = self._get_or_create_bucket(self.s3_bucket)
        return self._bucket

    @property
    def entries(self):
        """
        Get the locally cached files for the bucket.
        """
        if not self._entries:
            self._entries = dict((entry.key, entry)
                                 for entry in self.bucket.list(prefix=self.prefix))
        return self._entries

    def _get_or_create_bucket(self, name):
        """
        Retrieves a bucket if it exists, otherwise creates it.
        """
        try:
            return self.connection.get_bucket(name)
        except Exception as e:
            raise Exception("Bucket %s does not exist, or is inaccessible: %s." % (name, e))

    def _open(self, name, mode='rb'):
        name = self.get_name(name)
        f = S3BotoStorageFile(name, mode, self)
        if not f.key:
            raise IOError('File does not exist: %s' % name)
        return f

    def _save(self, name, content):
        name = self.get_name(name)
        key = self.bucket.new_key(name)
        key.set_contents_from_file(content)
        key.make_public()
        return name

    def exists(self, name):
        name = self.get_name(name)
        if self.entries:
            return name in self.entries
        k = self.bucket.new_key(name)
        return k.exists()

    def path(self, name):
        name = self.get_name(name)
        return os.path.join(self.location, name)

    def url(self, name):
        name = self.get_name(name)
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urljoin(self.base_url, filepath_to_uri(name))

    def get_name(self, name):
        import os
        return os.path.join(self.prefix, name)

    def _encode_name(self, name):
        return name.encode('utf-8')


class S3BotoStorageFile(File):
    """
    The default file object used by the S3BotoStorage backend.

    This file implements file streaming using boto's multipart
    uploading functionality. The file can be opened in read or
    write mode.
    This class extends Django's File class. However, the contained
    data is only the data contained in the current buffer. So you
    should not access the contained file object directly. You should
    access the data via this class.
    Warning: This file *must* be closed using the close() method in
    order to properly write the file to S3. Be sure to close the file
    in your application.

    This is ported from iserko's "django-storages"
    (https://github.com/iserko/django-storages/blob/master/storages/backends/s3boto.py)
    Modified to work with flask_imagekit
    """

    def __init__(self, name, mode, storage, buffer_size=5242880):
        self._storage = storage
        self.name = name[len(self._storage.location):].lstrip('/')
        self._mode = mode
        self.key = storage.bucket.get_key(self._storage._encode_name(name))
        if not self.key and 'w' in mode:
            self.key = storage.bucket.new_key(storage._encode_name(name))
        self._is_dirty = False
        self._file = None
        self._multipart = None
        # 5 MB is the minimum part size (if there is more than one part).
        # Amazon allows up to 10,000 parts.  The default supports uploads
        # up to roughly 50 GB.  Increase the part size to accommodate
        # for files larger than this.
        self._write_buffer_size = buffer_size
        self._write_counter = 0

    @property
    def size(self):
        return self.key.size

    @property
    def file(self):
        if self._file is None:
            self._file = StringIO()
            if 'r' in self._mode:
                self._is_dirty = False
                self.key.get_contents_to_file(self._file)
                self._file.seek(0)
        return self._file

    def read(self, *args, **kwargs):
        if 'r' not in self._mode:
            raise AttributeError("File was not opened in read mode.")
        return super(S3BotoStorageFile, self).read(*args, **kwargs)

    def write(self, *args, **kwargs):
        if 'w' not in self._mode:
            raise AttributeError("File was not opened in write mode.")
        self._is_dirty = True
        if self._multipart is None:
            provider = self.key.bucket.connection.provider
            upload_headers = {
                provider.acl_header: self._storage.acl
            }
            upload_headers.update(self._storage.headers)
            self._multipart = self._storage.bucket.initiate_multipart_upload(
                self.key.name,
                headers = upload_headers,
                reduced_redundancy = self._storage.reduced_redundancy
            )
        if self._write_buffer_size <= self._buffer_file_size:
            self._flush_write_buffer()
        return super(S3BotoStorageFile, self).write(*args, **kwargs)

    @property
    def _buffer_file_size(self):
        pos = self.file.tell()
        self.file.seek(0,os.SEEK_END)
        length = self.file.tell()
        self.file.seek(pos)
        return length

    def _flush_write_buffer(self):
        """
        Flushes the write buffer.
        """
        if self._buffer_file_size:
            self._write_counter += 1
            self.file.seek(0)
            self._multipart.upload_part_from_file(
                self.file,
                self._write_counter,
                headers=self._storage.headers
            )
            self.file.close()
            self._file = None

    def close(self):
        if self._is_dirty:
            self._flush_write_buffer()
            self._multipart.complete_upload()
        else:
            if not self._multipart is None:
                self._multipart.cancel_upload()
        self.key.close()

