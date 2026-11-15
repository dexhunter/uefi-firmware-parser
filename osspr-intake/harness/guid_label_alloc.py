'''Allocations made by FirmwareObject.guid_label on a large object tree.

iterate_objects() -> info() asks every file and section for guid_label.
That property formats the 16 raw bytes through sguid: a new struct format
string, an unpack tuple, eight '%02x' pieces, a join, and the dashed string.
Listing a BIOS (uefi_guids, or to_dict of a whole image) does this once per
object. 2500 objects is a DXE volume of drivers plus their sections.
'''

import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import alloccount  # noqa: E402

counter = alloccount.load()

from uefi_firmware.base import FirmwareObject  # noqa: E402

OBJECTS = 2500


class _Named(FirmwareObject):
    def __init__(self, guid):
        FirmwareObject.__init__(self)
        self.guid = guid


def _expected(guid):
    '''The same text sguid produces, computed without calling it.'''
    first, second, third, tail = __import__("struct").unpack("<IHH8s", guid)
    tail = "".join("%02x" % byte for byte in tail)
    return "%08x-%04x-%04x-%s-%s" % (first, second, third, tail[:4], tail[4:])


GUIDS = [
    uuid.UUID(int=(index * 0x9E3779B97F4A7C15) & ((1 << 128) - 1)).bytes_le
    for index in range(1, OBJECTS + 1)
]
OBJS = [_Named(guid) for guid in GUIDS]
if OBJS[0].guid_label != _expected(GUIDS[0]) or OBJS[-1].guid_label != _expected(GUIDS[-1]):
    raise SystemExit("guid_label disagrees with the canonical GUID text")


def run():
    for obj in OBJS:
        obj.guid_label


def main():
    run()
    counter.reset()
    run()
    print(counter.get())


if __name__ == "__main__":
    main()
