"""Tests for the hand-rolled protobuf encoding/decoding (joule_proto.py)."""
from __future__ import annotations

import struct

import pytest

from custom_components.joule_sous_vide.joule_proto import (
    # Wire primitives
    WIRETYPE_FIXED32,
    WIRETYPE_LENGTH_DELIMITED,
    WIRETYPE_VARINT,
    decode_fields,
    decode_varint,
    encode_field_bytes,
    encode_field_fixed32,
    encode_field_float,
    encode_field_varint,
    encode_tag,
    encode_varint,
    # Enums
    ErrorState,
    ProgramStep,
    ProgramType,
    # Dataclasses
    BeginLiveFeedRequest,
    CirculatorDataPoint,
    CirculatorProgram,
    StartProgramRequest,
    StopCirculatorRequest,
    StreamMessage,
    # Encode functions
    encode_begin_live_feed_request,
    encode_circulator_program,
    encode_start_program_request,
    encode_stop_circulator_request,
    encode_stream_message,
    # Decode functions
    decode_circulator_data_point,
    decode_stream_message,
    # High-level API
    build_live_feed_message,
    build_start_cook_message,
    build_stop_cook_message,
    parse_notification,
    # Exceptions
    JouleProtoError,
)


# ---------------------------------------------------------------------------
# Varint primitives
# ---------------------------------------------------------------------------


class TestEncodeVarint:
    def test_zero(self):
        assert encode_varint(0) == b"\x00"

    def test_single_byte(self):
        assert encode_varint(1) == b"\x01"
        assert encode_varint(127) == b"\x7f"

    def test_multibyte(self):
        # 300 = 0b100101100 -> 0xAC 0x02
        assert encode_varint(300) == b"\xac\x02"

    def test_large_value(self):
        # 16384 = 0x4000 -> 0x80 0x80 0x01
        assert encode_varint(16384) == b"\x80\x80\x01"


class TestDecodeVarint:
    def test_single_byte(self):
        assert decode_varint(b"\x01", 0) == (1, 1)

    def test_multibyte(self):
        assert decode_varint(b"\xac\x02", 0) == (300, 2)

    def test_with_offset(self):
        data = b"\xff\xac\x02"
        assert decode_varint(data, 1) == (300, 3)

    def test_zero(self):
        assert decode_varint(b"\x00", 0) == (0, 1)

    def test_truncated_raises(self):
        # 0x80 has continuation bit but no following byte
        with pytest.raises(JouleProtoError, match="Truncated"):
            decode_varint(b"\x80", 0)

    def test_empty_raises(self):
        with pytest.raises(JouleProtoError, match="Truncated"):
            decode_varint(b"", 0)


# ---------------------------------------------------------------------------
# Tag encoding
# ---------------------------------------------------------------------------


class TestEncodeTag:
    def test_field_1_varint(self):
        # (1 << 3) | 0 = 0x08
        assert encode_tag(1, WIRETYPE_VARINT) == b"\x08"

    def test_field_10_fixed32(self):
        # (10 << 3) | 5 = 85 = 0x55
        assert encode_tag(10, WIRETYPE_FIXED32) == b"\x55"

    def test_field_5_length_delimited(self):
        # (5 << 3) | 2 = 42 = 0x2a
        assert encode_tag(5, WIRETYPE_LENGTH_DELIMITED) == b"\x2a"

    def test_high_field_number(self):
        # field 90, wire type 2 -> (90 << 3) | 2 = 722
        tag = encode_tag(90, WIRETYPE_LENGTH_DELIMITED)
        decoded, _ = decode_varint(tag, 0)
        assert decoded == (90 << 3) | 2


# ---------------------------------------------------------------------------
# Field encoding helpers
# ---------------------------------------------------------------------------


class TestFieldEncoding:
    def test_field_varint(self):
        encoded = encode_field_varint(1, 1)
        assert encoded == b"\x08\x01"

    def test_field_float(self):
        encoded = encode_field_float(10, 65.0)
        tag = encode_tag(10, WIRETYPE_FIXED32)
        assert encoded == tag + struct.pack("<f", 65.0)

    def test_field_fixed32(self):
        encoded = encode_field_fixed32(1, 0)
        tag = encode_tag(1, WIRETYPE_FIXED32)
        assert encoded == tag + b"\x00\x00\x00\x00"

    def test_field_bytes(self):
        encoded = encode_field_bytes(5, b"\xaa\xbb")
        tag = encode_tag(5, WIRETYPE_LENGTH_DELIMITED)
        assert encoded == tag + b"\x02\xaa\xbb"

    def test_field_bytes_empty(self):
        encoded = encode_field_bytes(5, b"")
        tag = encode_tag(5, WIRETYPE_LENGTH_DELIMITED)
        assert encoded == tag + b"\x00"


# ---------------------------------------------------------------------------
# decode_fields generic parser
# ---------------------------------------------------------------------------


class TestDecodeFields:
    def test_empty(self):
        assert decode_fields(b"") == []

    def test_single_varint(self):
        data = encode_field_varint(1, 42)
        fields = decode_fields(data)
        assert len(fields) == 1
        assert fields[0] == (1, WIRETYPE_VARINT, 42)

    def test_single_float(self):
        data = encode_field_float(10, 65.0)
        fields = decode_fields(data)
        assert len(fields) == 1
        fn, wt, val = fields[0]
        assert fn == 10
        assert wt == WIRETYPE_FIXED32
        assert struct.unpack("<f", val)[0] == pytest.approx(65.0)

    def test_single_bytes(self):
        data = encode_field_bytes(5, b"\xaa")
        fields = decode_fields(data)
        assert len(fields) == 1
        assert fields[0] == (5, WIRETYPE_LENGTH_DELIMITED, b"\xaa")

    def test_multiple_fields(self):
        data = encode_field_varint(1, 10) + encode_field_float(2, 3.14)
        fields = decode_fields(data)
        assert len(fields) == 2
        assert fields[0][0] == 1
        assert fields[1][0] == 2

    def test_truncated_fixed32_raises(self):
        # Tag for field 1 fixed32, but only 2 bytes of data
        data = encode_tag(1, WIRETYPE_FIXED32) + b"\x00\x00"
        with pytest.raises(JouleProtoError, match="Truncated fixed32"):
            decode_fields(data)

    def test_truncated_length_delimited_raises(self):
        # Tag + length says 10 bytes, but only 2 available
        data = encode_tag(1, WIRETYPE_LENGTH_DELIMITED) + encode_varint(10) + b"\x00\x00"
        with pytest.raises(JouleProtoError, match="Truncated"):
            decode_fields(data)

    def test_unsupported_wire_type_raises(self):
        # Wire type 3 (start group, deprecated) — encode manually
        data = encode_varint((1 << 3) | 3)
        with pytest.raises(JouleProtoError, match="Unsupported wire type"):
            decode_fields(data)


# ---------------------------------------------------------------------------
# CirculatorProgram encoding
# ---------------------------------------------------------------------------


class TestCirculatorProgram:
    def test_basic(self):
        program = CirculatorProgram(set_point=65.0, cook_time=3600)
        data = encode_circulator_program(program)
        fields = decode_fields(data)
        field_map = {fn: (wt, val) for fn, wt, val in fields}

        # Field 1: set_point (float)
        assert 1 in field_map
        assert struct.unpack("<f", field_map[1][1])[0] == pytest.approx(65.0)

        # Field 2: cook_time (varint)
        assert 2 in field_map
        assert field_map[2][1] == 3600

    def test_zero_cook_time_omitted(self):
        program = CirculatorProgram(set_point=65.0, cook_time=0)
        data = encode_circulator_program(program)
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 2 not in field_numbers

    def test_manual_program_type_omitted(self):
        program = CirculatorProgram(set_point=65.0, program_type=ProgramType.MANUAL)
        data = encode_circulator_program(program)
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 5 not in field_numbers

    def test_automatic_program_type_included(self):
        program = CirculatorProgram(
            set_point=65.0, program_type=ProgramType.AUTOMATIC
        )
        data = encode_circulator_program(program)
        fields = decode_fields(data)
        field_map = {fn: (wt, val) for fn, wt, val in fields}
        assert 5 in field_map
        assert field_map[5][1] == ProgramType.AUTOMATIC


# ---------------------------------------------------------------------------
# StartProgramRequest / StopCirculatorRequest / BeginLiveFeedRequest
# ---------------------------------------------------------------------------


class TestStartProgramRequest:
    def test_wraps_program_as_field_1(self):
        program = CirculatorProgram(set_point=75.0, cook_time=5400)
        request = StartProgramRequest(circulator_program=program)
        data = encode_start_program_request(request)
        fields = decode_fields(data)

        assert len(fields) == 1
        fn, wt, val = fields[0]
        assert fn == 1
        assert wt == WIRETYPE_LENGTH_DELIMITED

        # Verify the embedded program can be parsed
        inner_fields = decode_fields(val)
        inner_map = {fn: (wt, v) for fn, wt, v in inner_fields}
        assert struct.unpack("<f", inner_map[1][1])[0] == pytest.approx(75.0)
        assert inner_map[2][1] == 5400


class TestStopCirculatorRequest:
    def test_empty(self):
        request = StopCirculatorRequest()
        data = encode_stop_circulator_request(request)
        assert data == b""


class TestBeginLiveFeedRequest:
    def test_encodes_feed_id(self):
        request = BeginLiveFeedRequest(feed_id=1)
        data = encode_begin_live_feed_request(request)
        fields = decode_fields(data)
        assert len(fields) == 1
        assert fields[0] == (1, WIRETYPE_VARINT, 1)


# ---------------------------------------------------------------------------
# CirculatorDataPoint decoding
# ---------------------------------------------------------------------------


class TestDecodeCirculatorDataPoint:
    def _build_data_point_bytes(
        self,
        bath_temp: float = 65.0,
        program_step: int = ProgramStep.COOK,
        time_remaining: int = 1800,
    ) -> bytes:
        """Build raw protobuf bytes for a CirculatorDataPoint."""
        data = b""
        data += encode_field_varint(1, 1)  # feed_id
        data += encode_field_varint(2, 42)  # sequence_number
        data += encode_field_varint(3, 1700000000)  # timestamp
        data += encode_field_varint(4, ErrorState.NO_ERROR)  # error_state
        data += encode_field_float(10, bath_temp)
        data += encode_field_varint(11, program_step)
        data += encode_field_varint(12, time_remaining)
        return data

    def test_full_decode(self):
        data = self._build_data_point_bytes(bath_temp=72.5, time_remaining=900)
        point = decode_circulator_data_point(data)

        assert point.feed_id == 1
        assert point.sequence_number == 42
        assert point.bath_temp == pytest.approx(72.5)
        assert point.program_step == ProgramStep.COOK
        assert point.time_remaining == 900
        assert point.error_state == ErrorState.NO_ERROR

    def test_partial_only_bath_temp(self):
        data = encode_field_float(10, 55.0)
        point = decode_circulator_data_point(data)
        assert point.bath_temp == pytest.approx(55.0)
        assert point.program_step == ProgramStep.UNKNOWN
        assert point.time_remaining == 0

    def test_unknown_fields_ignored(self):
        # Add an unknown field 99 (varint)
        data = encode_field_float(10, 60.0) + encode_field_varint(99, 12345)
        point = decode_circulator_data_point(data)
        assert point.bath_temp == pytest.approx(60.0)

    def test_pre_heat_step(self):
        data = self._build_data_point_bytes(program_step=ProgramStep.PRE_HEAT)
        point = decode_circulator_data_point(data)
        assert point.program_step == ProgramStep.PRE_HEAT


# ---------------------------------------------------------------------------
# StreamMessage encoding / decoding
# ---------------------------------------------------------------------------


class TestStreamMessageEncode:
    def test_with_start_program(self):
        program = CirculatorProgram(set_point=75.0, cook_time=3600)
        msg = StreamMessage(
            sender_address=b"\x01" * 6,
            recipient_address=b"\x02" * 6,
            start_program_request=StartProgramRequest(circulator_program=program),
        )
        data = encode_stream_message(msg)
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]

        assert 1 in field_numbers  # handle
        assert 5 in field_numbers  # sender_address
        assert 6 in field_numbers  # recipient_address
        assert 50 in field_numbers  # start_program_request

    def test_with_stop(self):
        msg = StreamMessage(
            stop_circulator_request=StopCirculatorRequest(),
        )
        data = encode_stream_message(msg)
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 60 in field_numbers

    def test_with_live_feed(self):
        msg = StreamMessage(
            begin_live_feed_request=BeginLiveFeedRequest(feed_id=1),
        )
        data = encode_stream_message(msg)
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 70 in field_numbers

    def test_addresses_included(self):
        msg = StreamMessage(
            sender_address=b"\xaa\xbb\xcc\xdd\xee\xff",
            recipient_address=b"\x11\x22\x33\x44\x55\x66",
        )
        data = encode_stream_message(msg)
        fields = decode_fields(data)
        field_map = {fn: val for fn, _, val in fields}
        assert field_map[5] == b"\xaa\xbb\xcc\xdd\xee\xff"
        assert field_map[6] == b"\x11\x22\x33\x44\x55\x66"


class TestStreamMessageDecode:
    def test_with_data_point(self):
        """Decode a StreamMessage containing a CirculatorDataPoint."""
        # Build the inner data point
        inner = encode_field_float(10, 68.5) + encode_field_varint(11, ProgramStep.COOK)

        # Build the outer StreamMessage
        data = (
            encode_field_fixed32(1, 0)  # handle
            + encode_field_bytes(5, b"\x01" * 6)  # sender
            + encode_field_bytes(6, b"\x02" * 6)  # recipient
            + encode_field_bytes(90, inner)  # circulator_data_point
        )

        msg = decode_stream_message(data)
        assert msg.circulator_data_point is not None
        assert msg.circulator_data_point.bath_temp == pytest.approx(68.5)
        assert msg.circulator_data_point.program_step == ProgramStep.COOK
        assert msg.sender_address == b"\x01" * 6

    def test_unknown_contents_ignored(self):
        """Unknown oneof fields do not cause errors."""
        # Field 153 (IdentifyCirculatorReply) — not modelled
        data = (
            encode_field_fixed32(1, 0)
            + encode_field_bytes(153, b"\x0a\x05Joule")
        )
        msg = decode_stream_message(data)
        assert msg.circulator_data_point is None

    def test_handle_decoded(self):
        data = encode_field_fixed32(1, 42)
        msg = decode_stream_message(data)
        assert msg.handle == 42

    def test_end_flag(self):
        data = encode_field_fixed32(1, 0) + encode_field_varint(4, 1)
        msg = decode_stream_message(data)
        assert msg.end is True


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------


class TestBuildStartCookMessage:
    def test_returns_bytes(self):
        result = build_start_cook_message(75.0, 3600)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_roundtrip_set_point(self):
        """Encode a start-cook message, decode it, verify set_point survives."""
        data = build_start_cook_message(75.0, 5400)
        fields = decode_fields(data)

        # Find the StartProgramRequest (field 50)
        start_req_bytes = None
        for fn, wt, val in fields:
            if fn == 50 and wt == WIRETYPE_LENGTH_DELIMITED:
                start_req_bytes = val
                break
        assert start_req_bytes is not None

        # Parse the embedded CirculatorProgram (field 1 inside StartProgramRequest)
        inner_fields = decode_fields(start_req_bytes)
        program_bytes = None
        for fn, wt, val in inner_fields:
            if fn == 1 and wt == WIRETYPE_LENGTH_DELIMITED:
                program_bytes = val
                break
        assert program_bytes is not None

        # Verify set_point
        program_fields = decode_fields(program_bytes)
        program_map = {fn: (wt, v) for fn, wt, v in program_fields}
        assert struct.unpack("<f", program_map[1][1])[0] == pytest.approx(75.0)
        assert program_map[2][1] == 5400


class TestBuildStopCookMessage:
    def test_returns_bytes(self):
        result = build_stop_cook_message()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_contains_field_60(self):
        data = build_stop_cook_message()
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 60 in field_numbers


class TestBuildLiveFeedMessage:
    def test_returns_bytes(self):
        result = build_live_feed_message()
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_contains_field_70(self):
        data = build_live_feed_message()
        fields = decode_fields(data)
        field_numbers = [fn for fn, _, _ in fields]
        assert 70 in field_numbers


class TestParseNotification:
    def test_with_data_point(self):
        """parse_notification returns CirculatorDataPoint when present."""
        inner = encode_field_float(10, 68.5)
        data = encode_field_fixed32(1, 0) + encode_field_bytes(90, inner)

        result = parse_notification(data)
        assert result is not None
        assert result.bath_temp == pytest.approx(68.5)

    def test_with_non_data_point(self):
        """parse_notification returns None for messages without data point."""
        data = encode_field_fixed32(1, 0) + encode_field_bytes(153, b"\x0a\x05Joule")
        result = parse_notification(data)
        assert result is None

    def test_with_garbage(self):
        """parse_notification returns None for malformed data."""
        result = parse_notification(b"\xff\xff\xff")
        assert result is None

    def test_with_empty(self):
        """parse_notification returns None for empty data."""
        result = parse_notification(b"")
        assert result is None
