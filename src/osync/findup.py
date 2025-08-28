import os


def findup(filename: str):
    cwd = os.getcwd()

    def inner(drive: str, dir: str, filename: str) -> str:
        filepath = os.path.join(drive, dir, filename)
        if os.path.isfile(filepath):
            return filepath
        if dir == os.path.sep:
            raise LookupError("file not found: %s" % filename)
        return inner(drive, os.path.dirname(dir), filename)

    drive, start = os.path.splitdrive(os.path.abspath(cwd))
    return inner(drive, start, filename)
