class HandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def is_dir(self, *args, **kwargs):
        raise NotImplementedError("is_dir not implemented in child class")

    def is_symlink(self, *args, **kwargs):
        raise NotImplementedError("is_symlink not implemented in child class")

    def file_contents(self, *args, **kwargs):
        raise NotImplementedError("file_contents not implemented in child class")

    def readdir(self, *args, **kwargs):
        raise NotImplementedError("readdir not implemented in child class")
