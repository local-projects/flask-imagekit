from ..cachefiles import LazyImageCacheFile

class SourceGroupFilesGenerator(object):
    """
    A Python generator that yields cache file objects for source groups.

    """
    def __init__(self, source_group, generator_id):
        self.source_group = source_group
        self.generator_id = generator_id

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.source_group, self.generator_id))

    def __call__(self):
        for source_file in self.source_group.files():
            yield LazyImageCacheFile(self.generator_id,
                                              source=source_file)
