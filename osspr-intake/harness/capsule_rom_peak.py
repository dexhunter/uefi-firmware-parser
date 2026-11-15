'''Peak traced memory of FirmwareCapsule.process_rom_image.

An Aptio capsule's body is a whole SPI image. process_rom_image slices that
body into a new bytes object before MultiVolumeContainer parses it, so the
image is live twice. Eight mebibytes is a small but real BIOS region; the
slice is the copy a memoryview would not make. The two volumes are real FFS2
headers so the parse result is the same one the capsule tests check.
'''

import os
import struct
import sys
import tracemalloc
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from uefi_firmware.structs.uefi_structs import (  # noqa: E402
    APTIO_SIGNED_CAPSULE_GUID,
    FIRMWARE_VOLUME_GUIDS,
)
from uefi_firmware.uefi import FirmwareCapsule, FirmwareVolume  # noqa: E402

# A small SPI image: option ROM padding is erased flash, and the BIOS region
# is what vendors ship inside an Aptio capsule.
ROM_BYTES = 8 * 1024 * 1024


def _volume(size):
    block_map = struct.pack("<II", 1, size) + b"\x00" * 8
    hdrlen = FirmwareVolume._HEADER_SIZE + len(block_map)
    header = struct.pack(
        "<16s16sQ4sIHHHsB",
        b"\x00" * 16,
        uuid.UUID(FIRMWARE_VOLUME_GUIDS["FFS2"]).bytes_le,
        size,
        b"_FVH",
        0,
        hdrlen,
        0,
        0,
        b"\x00",
        2,
    )
    return header + block_map + b"\xff" * (size - hdrlen)


def _capsule():
    rom = _volume(0x10000) + b"\x00" * 0x1000 + _volume(0x10000)
    rom += b"\xff" * (ROM_BYTES - len(rom))
    header_size = 0x40
    header = uuid.UUID(APTIO_SIGNED_CAPSULE_GUID).bytes_le + struct.pack(
        "<IIIHH", header_size, 0, header_size + len(rom), header_size, 0)
    return header.ljust(header_size, b"\x00") + rom


def main():
    capsule = FirmwareCapsule(_capsule())
    if not capsule.valid_header or not capsule.is_aptio():
        raise SystemExit("capsule header was not recognized")
    tracemalloc.start()
    tracemalloc.reset_peak()
    parsed = capsule.process_rom_image()
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if parsed is not True or len(capsule.capsule_body.volumes) != 2:
        raise SystemExit("ROM image did not parse as two volumes")
    print(peak)


if __name__ == "__main__":
    main()
