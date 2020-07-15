import contextlib
import os
import tempfile


# https://stackoverflow.com/a/57701186
@contextlib.contextmanager
def temporary_named_file(content, suffix=None):
    if isinstance(content, str):
        content = str.encode(content)

    f = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    f.write(content)
    f.close()
    yield f.name
    os.remove(f.name)
