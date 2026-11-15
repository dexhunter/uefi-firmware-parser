'''Allocations made by get_guid_name on a full-image GUID workload.

A vendor BIOS names hundreds of file and DEPEX GUIDs. The bundled tables hold
2255 entries. get_guid_name rebuilds every table with list(items()) and walks
it as a Python list of ints, so an unknown GUID allocates thousands of
short-lived objects. Known GUIDs still rebuild every table before the hit.
'''

import os
import struct
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import alloccount  # noqa: E402

counter = alloccount.load()

from uefi_firmware.guids import GUID_TABLES, get_guid_name  # noqa: E402

# 150 names that are in the tables, then 400 that are not. A full AMI/Lenovo
# image is in this range: EDK2 drivers that are listed, and OEM files that are
# not. Order is fixed so the scan does the same work every run.
KNOWN = 150
UNKNOWN = 400


def _pack(parts):
    first, second, third = parts[:3]
    return struct.pack("<IHH", first, second, third) + bytes(parts[3:])


def _workload():
    known = []
    for table in GUID_TABLES:
        for name, parts in table.items():
            if len(known) >= KNOWN:
                break
            # A few names share one value; keep the one the scan returns.
            if len(parts) != 11:
                continue
            raw = _pack(parts)
            if get_guid_name(raw) != name:
                continue
            known.append(raw)
        if len(known) >= KNOWN:
            break
    if len(known) != KNOWN:
        raise SystemExit("GUID tables are smaller than the workload")
    unknown = []
    for index in range(1, UNKNOWN + 1):
        raw = uuid.UUID(int=(index * 0x9E3779B97F4A7C15) & ((1 << 128) - 1)).bytes_le
        if get_guid_name(raw) is not None:
            raise SystemExit("synthetic GUID collided with a table entry")
        unknown.append(raw)
    return known + unknown


GUIDS = _workload()


def run():
    for guid in GUIDS:
        get_guid_name(guid)


def main():
    run()
    counter.reset()
    run()
    print(counter.get())


if __name__ == "__main__":
    main()
