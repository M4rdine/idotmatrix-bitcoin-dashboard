"""Chunk large BLE payloads into 4096-byte blocks.

The iDotMatrix device has a maximum BLE write size. Large payloads
(like image data) must be split into chunks that fit within this limit.
Each chunk is sent as a separate BLE write operation.
"""

from __future__ import annotations

MAX_CHUNK_SIZE = 4096


def chunk_payload(data: bytearray | bytes, chunk_size: int = MAX_CHUNK_SIZE) -> list[bytearray]:
    """Split a payload into chunks of at most chunk_size bytes.

    Args:
        data: The full payload to chunk (header + pixel data).
        chunk_size: Maximum bytes per chunk (default: 4096).

    Returns:
        List of bytearray chunks, each at most chunk_size bytes.

    Raises:
        ValueError: If data is empty or chunk_size is not positive.
    """
    if not data:
        raise ValueError("Cannot chunk empty data")
    if chunk_size <= 0:
        raise ValueError(f"Chunk size must be positive, got {chunk_size}")

    chunks: list[bytearray] = []
    offset = 0
    data_len = len(data)

    while offset < data_len:
        end = min(offset + chunk_size, data_len)
        chunks.append(bytearray(data[offset:end]))
        offset = end

    return chunks


def calculate_chunk_count(data_length: int, chunk_size: int = MAX_CHUNK_SIZE) -> int:
    """Calculate how many chunks a payload will be split into.

    Args:
        data_length: Total payload size in bytes.
        chunk_size: Maximum bytes per chunk.

    Returns:
        Number of chunks needed.
    """
    if data_length <= 0:
        return 0
    return (data_length + chunk_size - 1) // chunk_size
