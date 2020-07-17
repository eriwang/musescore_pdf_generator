import os


def get_no_extension(filename):
    return os.path.splitext(filename)[0]


def get_extension(filename):
    return os.path.splitext(filename)[1]
