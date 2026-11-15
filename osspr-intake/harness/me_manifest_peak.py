'''Peak traced memory of MeManifestHeader.__init__ on a code partition.

The manifest header is a few hundred bytes. The rest of an FTPR/NFTP
partition is the code and modules, often multiple mebibytes. __init__ keeps
that tail with data[partition_offset:], which copies it. The caller already
holds the partition (the ME container does). Four mebibytes is a realistic
code partition, and the copy is what a memoryview of the same buffer would
not allocate.
'''

import os
import sys
import tracemalloc

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from uefi_firmware.me import MeManifestHeader  # noqa: E402
from uefi_firmware.structs.intel_me_structs import MeManifestHeaderType  # noqa: E402

# Bytes after the manifest header. CSME code partitions are this size.
TAIL_BYTES = 4 * 1024 * 1024
_PARTITION_OFFSET = 0xA1 * 4 + 12


def _partition():
    manifest = MeManifestHeaderType()
    manifest.ModuleType = 4
    manifest.HeaderLen = 0xA1
    manifest.Size = TAIL_BYTES // 4
    manifest.Tag = b"$MN2"
    manifest.PartitionName = b"FTPR"
    # The same padding the unit tests use so the header meets HeaderLen.
    header = bytes(manifest).ljust(_PARTITION_OFFSET, b"\x00")
    return header + b"\xab" * TAIL_BYTES


def main():
    data = _partition()
    tracemalloc.start()
    tracemalloc.reset_peak()
    manifest = MeManifestHeader(data)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if not manifest.valid_header:
        raise SystemExit("manifest header was rejected")
    if manifest.data != data[manifest.partition_offset:]:
        raise SystemExit("manifest tail does not match the partition")
    if len(manifest.data) != TAIL_BYTES:
        raise SystemExit("manifest tail is %d bytes" % len(manifest.data))
    print(peak)


if __name__ == "__main__":
    main()
