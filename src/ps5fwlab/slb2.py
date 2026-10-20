"""Strict metadata-only parser for the observed SLB2 wrapper layout.

The parser never extracts, decrypts, or executes an entry. Unknown header
fields are retained as raw integers rather than assigned invented semantics.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from pathlib import Path


BLOCK_SIZE = 512
HEADER_SIZE = 0x20
ENTRY_SIZE = 0x30
MAX_ENTRIES = (BLOCK_SIZE - HEADER_SIZE) // ENTRY_SIZE


class SLB2Error(ValueError):
    """The input does not satisfy the bounded SLB2 layout."""


@dataclass(frozen=True)
class SLB2Entry:
    name: str
    block_offset: int
    offset: int
    size: int
    unknown_1: int
    unknown_2: int


@dataclass(frozen=True)
class SLB2Metadata:
    file_size: int
    version: int
    block_count: int
    unknown_1: int
    unknown_2: int
    unknown_3: int
    unknown_4: int
    entries: tuple[SLB2Entry, ...]


def _parse_name(raw: bytes) -> str:
    head, marker, padding = raw.partition(b"\x00")
    if not marker or not head or any(padding):
        raise SLB2Error("entry name must be NUL terminated with zero padding")
    try:
        name = head.decode("ascii")
    except UnicodeDecodeError as exc:
        raise SLB2Error("entry name is not ASCII") from exc
    if name in {".", ".."} or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in name):
        raise SLB2Error("entry name contains unsafe characters")
    return name


def parse_slb2(path: str | Path) -> SLB2Metadata:
    """Read only the first 512 bytes, validating all declared entry ranges."""

    with Path(path).open("rb") as source:
        file_size = os.fstat(source.fileno()).st_size
        if file_size < BLOCK_SIZE or file_size % BLOCK_SIZE:
            raise SLB2Error("file must contain complete 512-byte blocks")
        header_block = source.read(BLOCK_SIZE)
        if len(header_block) != BLOCK_SIZE:
            raise SLB2Error("short read of SLB2 header block")

    magic, version, unknown_1, entry_count, block_count, unknown_2, unknown_3, unknown_4 = struct.unpack_from(
        "<4s7I", header_block, 0
    )
    if magic != b"SLB2":
        raise SLB2Error("invalid SLB2 magic")
    if not 1 <= entry_count <= MAX_ENTRIES:
        raise SLB2Error("entry count exceeds first header block capacity")
    if block_count * BLOCK_SIZE != file_size:
        raise SLB2Error("declared block count does not match file size")

    entries: list[SLB2Entry] = []
    names: set[str] = set()
    for index in range(entry_count):
        table_offset = HEADER_SIZE + index * ENTRY_SIZE
        block_offset, size, entry_unknown_1, entry_unknown_2, name_bytes = struct.unpack_from(
            "<4I32s", header_block, table_offset
        )
        if not block_offset or not size:
            raise SLB2Error(f"entry {index} has zero offset or size")
        offset = block_offset * BLOCK_SIZE
        if offset < BLOCK_SIZE or offset >= file_size or size > file_size - offset:
            raise SLB2Error(f"entry {index} lies outside the file")
        name = _parse_name(name_bytes)
        if name in names:
            raise SLB2Error(f"entry {index} has a duplicate name")
        names.add(name)
        entries.append(
            SLB2Entry(
                name=name,
                block_offset=block_offset,
                offset=offset,
                size=size,
                unknown_1=entry_unknown_1,
                unknown_2=entry_unknown_2,
            )
        )

    ordered = sorted(entries, key=lambda entry: entry.offset)
    for left, right in zip(ordered, ordered[1:]):
        if left.offset + left.size > right.offset:
            raise SLB2Error("entries overlap")

    return SLB2Metadata(
        file_size=file_size,
        version=version,
        block_count=block_count,
        unknown_1=unknown_1,
        unknown_2=unknown_2,
        unknown_3=unknown_3,
        unknown_4=unknown_4,
        entries=tuple(entries),
    )
