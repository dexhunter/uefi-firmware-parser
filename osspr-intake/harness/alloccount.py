'''Build and load the object-allocation counter used by the intake harnesses.'''

import importlib.util
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "countalloc.c")


def load():
    '''Return the countalloc module, compiling it on first use.

    reset() zeroes the counter. get() returns how many object allocations
    have happened since reset, including the integer object get() itself
    creates for a non-interned count.
    '''
    tag = "py%s%s" % sys.version_info[:2]
    cached = os.path.join(tempfile.gettempdir(), "osspr-uefi-countalloc-%s.so" % tag)
    if not os.path.exists(cached) or os.path.getmtime(cached) < os.path.getmtime(_SRC):
        includes = subprocess.check_output(
            ["python3-config", "--includes"], text=True).split()
        subprocess.check_call(
            ["cc", "-shared", "-fPIC", "-O2", *includes, "-o", cached, _SRC])
    spec = importlib.util.spec_from_file_location("countalloc", cached)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
