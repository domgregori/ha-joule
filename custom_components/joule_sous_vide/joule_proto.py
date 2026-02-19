"""Hand-rolled protobuf encoding/decoding for the ChefSteps Joule protocol.

Only the message types used by this integration are implemented.
Field numbers and types are reverse-engineered from the Joule Android app:
https://github.com/li-dennis/chromeJoule/blob/master/dist/protobuf-files/base.proto

Wire format reference: https://protobuf.dev/programming-guides/encoding/
"""
from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Wire type constants
# ---------------------------------------------------------------------------
WIRETYPE_VARINT = 0
WIRETYPE_FIXED64 = 1
WIRETYPE_LENGTH_DELIMITED = 2
WIRETYPE_FIXED32 = 5

# ---------------------------------------------------------------------------
# StreamMessage oneof field numbers
# ---------------------------------------------------------------------------
FIELD_START_PROGRAM_REQUEST = 50
FIELD_STOP_CIRCULATOR_REQUEST = 60
FIELD_BEGIN_LIVE_FEED_REQUEST = 70
FIELD_CIRCULATOR_DATA_POINT = 90


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------
class JouleProtoError(Exception):
    """Raised for protobuf encoding/decoding failures."""


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class ProgramType(IntEnum):
    MANUAL = 0
    AUTOMATIC = 1


class ProgramStep(IntEnum):
    UNKNOWN = 0
    PRE_HEAT = 1
    WAIT_FOR_FOOD = 2
    COOK = 3
    WAIT_FOR_REMOVE_FOOD = 4
    ERROR = 5


class ErrorState(IntEnum):
    NO_ERROR = 0
    SOFT_ERROR = 1
    HARD_ERROR = 2


# ---------------------------------------------------------------------------
# Wire-format primitives
# ---------------------------------------------------------------------------
def encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as a protobuf varint."""
    parts: list[int] = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value & 0x7F)
    return bytes(parts)


def decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Decode a varint at *offset*. Returns ``(value, new_offset)``."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise JouleProtoError("Truncated varint")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            return result, offset
        shift += 7
        if shift >= 64:
            raise JouleProtoError("Varint too long")


def encode_tag(field_number: int, wire_type: int) -> bytes:
    """Encode a protobuf field tag."""
    return encode_varint((field_number << 3) | wire_type)


def encode_field_varint(field_number: int, value: int) -> bytes:
    """Encode a varint field (tag + value)."""
    return encode_tag(field_number, WIRETYPE_VARINT) + encode_varint(value)


def encode_field_float(field_number: int, value: float) -> bytes:
    """Encode a float field (tag + 4-byte LE IEEE 754)."""
    return encode_tag(field_number, WIRETYPE_FIXED32) + struct.pack("<f", value)


def encode_field_fixed32(field_number: int, value: int) -> bytes:
    """Encode a fixed32 field (tag + 4-byte LE unsigned int)."""
    return encode_tag(field_number, WIRETYPE_FIXED32) + struct.pack("<I", value)


def encode_field_bytes(field_number: int, value: bytes) -> bytes:
    """Encode a length-delimited field (tag + length + value)."""
    return (
        encode_tag(field_number, WIRETYPE_LENGTH_DELIMITED)
        + encode_varint(len(value))
        + value
    )


def decode_fields(data: bytes) -> list[tuple[int, int, Any]]:
    """Parse raw protobuf bytes into ``(field_number, wire_type, value)`` tuples.

    For varint fields ``value`` is an ``int``.
    For fixed32 fields ``value`` is 4 raw bytes.
    For fixed64 fields ``value`` is 8 raw bytes.
    For length-delimited fields ``value`` is raw ``bytes``.
    """
    fields: list[tuple[int, int, Any]] = []
    offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        wire_type = tag & 0x07
        field_number = tag >> 3

        if wire_type == WIRETYPE_VARINT:
            value, offset = decode_varint(data, offset)
        elif wire_type == WIRETYPE_FIXED32:
            if offset + 4 > len(data):
                raise JouleProtoError("Truncated fixed32")
            value = data[offset : offset + 4]
            offset += 4
        elif wire_type == WIRETYPE_FIXED64:
            if offset + 8 > len(data):
                raise JouleProtoError("Truncated fixed64")
            value = data[offset : offset + 8]
            offset += 8
        elif wire_type == WIRETYPE_LENGTH_DELIMITED:
            length, offset = decode_varint(data, offset)
            if offset + length > len(data):
                raise JouleProtoError("Truncated length-delimited field")
            value = data[offset : offset + length]
            offset += length
        else:
            raise JouleProtoError(f"Unsupported wire type {wire_type}")

        fields.append((field_number, wire_type, value))
    return fields


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class CirculatorProgram:
    """Cook program parameters."""

    set_point: float  # field 1, float — target temp in Celsius
    cook_time: int = 0  # field 2, uint32 — seconds (0 = unlimited)
    program_type: ProgramType = ProgramType.MANUAL  # field 5, enum


@dataclass
class StartProgramRequest:
    """Start a cooking program."""

    circulator_program: CirculatorProgram  # field 1, embedded message


@dataclass
class StopCirculatorRequest:
    """Stop the active cooking program (empty body)."""


@dataclass
class BeginLiveFeedRequest:
    """Request a live data feed from the device."""

    feed_id: int = 1  # field 1, uint32


@dataclass
class CirculatorDataPoint:
    """Real-time sensor readings from the device."""

    feed_id: int = 0  # field 1, uint32
    sequence_number: int = 0  # field 2, uint32
    timestamp: int = 0  # field 3, uint32
    error_state: ErrorState = ErrorState.NO_ERROR  # field 4, enum
    bath_temp: float = 0.0  # field 10, float
    program_step: ProgramStep = ProgramStep.UNKNOWN  # field 11, enum
    time_remaining: int = 0  # field 12, uint32


@dataclass
class StreamMessage:
    """Root envelope for all Joule BLE messages."""

    handle: int = 0  # field 1, fixed32
    end: bool = False  # field 4, bool
    sender_address: bytes = b""  # field 5, bytes
    recipient_address: bytes = b""  # field 6, bytes
    # oneof contents — at most one of these is set:
    start_program_request: StartProgramRequest | None = None  # field 50
    stop_circulator_request: StopCirculatorRequest | None = None  # field 60
    begin_live_feed_request: BeginLiveFeedRequest | None = None  # field 70
    circulator_data_point: CirculatorDataPoint | None = None  # field 90


# ---------------------------------------------------------------------------
# Encoding functions
# ---------------------------------------------------------------------------
def encode_circulator_program(program: CirculatorProgram) -> bytes:
    """Encode a CirculatorProgram to protobuf bytes."""
    result = encode_field_float(1, program.set_point)
    if program.cook_time > 0:
        result += encode_field_varint(2, program.cook_time)
    if program.program_type != ProgramType.MANUAL:
        result += encode_field_varint(5, program.program_type)
    return result


def encode_start_program_request(request: StartProgramRequest) -> bytes:
    """Encode a StartProgramRequest to protobuf bytes."""
    program_bytes = encode_circulator_program(request.circulator_program)
    return encode_field_bytes(1, program_bytes)


def encode_stop_circulator_request(_request: StopCirculatorRequest) -> bytes:
    """Encode a StopCirculatorRequest (empty body)."""
    return b""


def encode_begin_live_feed_request(request: BeginLiveFeedRequest) -> bytes:
    """Encode a BeginLiveFeedRequest to protobuf bytes."""
    return encode_field_varint(1, request.feed_id)


def encode_stream_message(message: StreamMessage) -> bytes:
    """Encode a complete StreamMessage envelope."""
    result = encode_field_fixed32(1, message.handle)
    if message.end:
        result += encode_field_varint(4, 1)
    if message.sender_address:
        result += encode_field_bytes(5, message.sender_address)
    if message.recipient_address:
        result += encode_field_bytes(6, message.recipient_address)

    # Encode the oneof contents
    if message.start_program_request is not None:
        inner = encode_start_program_request(message.start_program_request)
        result += encode_field_bytes(FIELD_START_PROGRAM_REQUEST, inner)
    elif message.stop_circulator_request is not None:
        inner = encode_stop_circulator_request(message.stop_circulator_request)
        result += encode_field_bytes(FIELD_STOP_CIRCULATOR_REQUEST, inner)
    elif message.begin_live_feed_request is not None:
        inner = encode_begin_live_feed_request(message.begin_live_feed_request)
        result += encode_field_bytes(FIELD_BEGIN_LIVE_FEED_REQUEST, inner)

    return result


# ---------------------------------------------------------------------------
# Decoding functions
# ---------------------------------------------------------------------------
def decode_circulator_data_point(data: bytes) -> CirculatorDataPoint:
    """Decode a CirculatorDataPoint from raw protobuf bytes."""
    point = CirculatorDataPoint()
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == WIRETYPE_VARINT:
            point.feed_id = value
        elif field_number == 2 and wire_type == WIRETYPE_VARINT:
            point.sequence_number = value
        elif field_number == 3 and wire_type == WIRETYPE_VARINT:
            point.timestamp = value
        elif field_number == 4 and wire_type == WIRETYPE_VARINT:
            point.error_state = ErrorState(value)
        elif field_number == 10 and wire_type == WIRETYPE_FIXED32:
            point.bath_temp = struct.unpack("<f", value)[0]
        elif field_number == 11 and wire_type == WIRETYPE_VARINT:
            point.program_step = ProgramStep(value)
        elif field_number == 12 and wire_type == WIRETYPE_VARINT:
            point.time_remaining = value
        # Unknown fields are silently ignored
    return point


def decode_stream_message(data: bytes) -> StreamMessage:
    """Decode a StreamMessage from raw protobuf bytes."""
    message = StreamMessage()
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == WIRETYPE_FIXED32:
            message.handle = struct.unpack("<I", value)[0]
        elif field_number == 4 and wire_type == WIRETYPE_VARINT:
            message.end = bool(value)
        elif field_number == 5 and wire_type == WIRETYPE_LENGTH_DELIMITED:
            message.sender_address = value
        elif field_number == 6 and wire_type == WIRETYPE_LENGTH_DELIMITED:
            message.recipient_address = value
        elif (
            field_number == FIELD_CIRCULATOR_DATA_POINT
            and wire_type == WIRETYPE_LENGTH_DELIMITED
        ):
            message.circulator_data_point = decode_circulator_data_point(value)
        # Other oneof fields (replies, keep-alive, etc.) are silently ignored
    return message


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------
_DEFAULT_ADDRESS = b"\x00" * 6


def build_start_cook_message(
    set_point_celsius: float,
    cook_time_seconds: int,
    sender: bytes = _DEFAULT_ADDRESS,
    recipient: bytes = _DEFAULT_ADDRESS,
) -> bytes:
    """Build a serialized StreamMessage containing a StartProgramRequest."""
    program = CirculatorProgram(
        set_point=set_point_celsius,
        cook_time=cook_time_seconds,
        program_type=ProgramType.MANUAL,
    )
    msg = StreamMessage(
        sender_address=sender,
        recipient_address=recipient,
        start_program_request=StartProgramRequest(circulator_program=program),
    )
    return encode_stream_message(msg)


def build_stop_cook_message(
    sender: bytes = _DEFAULT_ADDRESS,
    recipient: bytes = _DEFAULT_ADDRESS,
) -> bytes:
    """Build a serialized StreamMessage containing a StopCirculatorRequest."""
    msg = StreamMessage(
        sender_address=sender,
        recipient_address=recipient,
        stop_circulator_request=StopCirculatorRequest(),
    )
    return encode_stream_message(msg)


def build_live_feed_message(
    feed_id: int = 1,
    sender: bytes = _DEFAULT_ADDRESS,
    recipient: bytes = _DEFAULT_ADDRESS,
) -> bytes:
    """Build a serialized StreamMessage containing a BeginLiveFeedRequest."""
    msg = StreamMessage(
        sender_address=sender,
        recipient_address=recipient,
        begin_live_feed_request=BeginLiveFeedRequest(feed_id=feed_id),
    )
    return encode_stream_message(msg)


def parse_notification(data: bytes) -> CirculatorDataPoint | None:
    """Parse a BLE notification as a StreamMessage.

    Returns the ``CirculatorDataPoint`` if present, otherwise ``None``.
    Malformed data is logged and returns ``None`` (never raises).
    """
    try:
        msg = decode_stream_message(data)
        return msg.circulator_data_point
    except (JouleProtoError, Exception):  # noqa: BLE001
        _LOGGER.debug("Failed to parse notification: %s", data.hex())
        return None
