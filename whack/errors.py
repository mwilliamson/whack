class WhackUserError(Exception):
    pass


class FileNotFoundError(WhackUserError):
    pass


class PackageNotAvailableError(WhackUserError):
    pass
