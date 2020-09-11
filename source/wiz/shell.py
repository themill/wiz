# :coding: utf-8

import sys
import collections
import subprocess


def convert(data):
    """Convert environment from unicode to string.

    Windows can not handle environment otherwise.

    """
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def popen(args, **kwargs):
    """Wrapper for `subprocess.Popen`.

    (Issue discovered and solved by REZ:
    https://github.com/nerdvegas/rez/blob/29611d25caa570a55e053b96e4bf941db1f38786/src/rez/utils/execution.py#L44)

    Avoids python bug described here: https://bugs.python.org/issue3905. This
    can arise when apps (maya) install a non-standard stdin handler.
    In newer version of maya and katana, the sys.stdin object can also become
    replaced by an object with no 'fileno' attribute, this is also taken into
    account.

    """
    if "stdin" not in kwargs:
        try:
            file_no = sys.stdin.fileno()
        except AttributeError:
            file_no = sys.__stdin__.fileno()

        if file_no not in (0, 1, 2):
            kwargs["stdin"] = subprocess.PIPE

    return subprocess.Popen(args, **kwargs)
