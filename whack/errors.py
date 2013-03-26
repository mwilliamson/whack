class WhackUserError(Exception):
    def __init__(self, message=None):
        Exception.__init__(self, message)
        self.message = message


class FileNotFoundError(WhackUserError):
    pass


class PackageNotAvailableError(WhackUserError):
    pass
