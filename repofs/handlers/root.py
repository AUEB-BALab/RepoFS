from repofs.handlers.handler_base import HandlerBase

class RootHandler(HandlerBase):
    def readdir(self):
        return ['commits-by-date', 'commits-by-hash', 'branches', 'tags']

    def is_dir(self):
        return True
