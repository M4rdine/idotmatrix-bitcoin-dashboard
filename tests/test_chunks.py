"""Tests for payload chunking."""

from __future__ import annotations

import pytest

from src.protocol.chunks import calculate_chunk_count, chunk_payload


class TestChunkPayload:
    def test_single_chunk(self) -> None:
        data = bytearray(100)
        chunks = chunk_payload(data, chunk_size=4096)
        assert len(chunks) == 1
        assert len(chunks[0]) == 100

    def test_exact_chunk_size(self) -> None:
        data = bytearray(4096)
        chunks = chunk_payload(data, chunk_size=4096)
        assert len(chunks) == 1

    def test_two_chunks(self) -> None:
        data = bytearray(4097)
        chunks = chunk_payload(data, chunk_size=4096)
        assert len(chunks) == 2
        assert len(chunks[0]) == 4096
        assert len(chunks[1]) == 1

    def test_many_chunks(self) -> None:
        data = bytearray(10000)
        chunks = chunk_payload(data, chunk_size=4096)
        assert len(chunks) == 3
        total = sum(len(c) for c in chunks)
        assert total == 10000

    def test_small_chunk_size(self) -> None:
        data = bytearray([1, 2, 3, 4, 5])
        chunks = chunk_payload(data, chunk_size=2)
        assert len(chunks) == 3
        assert chunks[0] == bytearray([1, 2])
        assert chunks[1] == bytearray([3, 4])
        assert chunks[2] == bytearray([5])

    def test_preserves_data(self) -> None:
        original = bytearray(range(256))
        chunks = chunk_payload(original, chunk_size=100)
        reassembled = bytearray()
        for chunk in chunks:
            reassembled.extend(chunk)
        assert reassembled == original

    def test_empty_data_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            chunk_payload(bytearray())

    def test_zero_chunk_size_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            chunk_payload(bytearray([1]), chunk_size=0)

    def test_accepts_bytes(self) -> None:
        data = bytes(100)
        chunks = chunk_payload(data, chunk_size=50)
        assert len(chunks) == 2

    def test_chunks_are_bytearrays(self) -> None:
        chunks = chunk_payload(bytearray(10), chunk_size=5)
        for chunk in chunks:
            assert isinstance(chunk, bytearray)

    def test_32x32_image_payload(self) -> None:
        """Simulate chunking a 32x32 RGB image with 9-byte header."""
        payload_size = 9 + (32 * 32 * 3)  # 3081 bytes
        data = bytearray(payload_size)
        chunks = chunk_payload(data)
        assert len(chunks) == 1  # fits in single chunk

    def test_64x64_image_payload(self) -> None:
        """Simulate chunking a 64x64 RGB image with 9-byte header."""
        payload_size = 9 + (64 * 64 * 3)  # 12297 bytes
        data = bytearray(payload_size)
        chunks = chunk_payload(data)
        assert len(chunks) == 4  # needs multiple chunks


class TestCalculateChunkCount:
    def test_zero_length(self) -> None:
        assert calculate_chunk_count(0) == 0

    def test_fits_in_one(self) -> None:
        assert calculate_chunk_count(100) == 1

    def test_exact_boundary(self) -> None:
        assert calculate_chunk_count(4096) == 1

    def test_just_over(self) -> None:
        assert calculate_chunk_count(4097) == 2

    def test_large_payload(self) -> None:
        assert calculate_chunk_count(12297) == 4
