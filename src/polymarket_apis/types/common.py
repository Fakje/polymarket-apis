from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, get_args, get_origin, Union, List, Dict

from dateutil import parser
from hexbytes import HexBytes
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator


class Base(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        strict=False,
        json_encoders={Decimal: str},  # Convert Decimal to string on serialization
    )

    @model_validator(mode='before')
    @classmethod
    def _convert_floats_to_decimals(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        converted_data = data.copy()
        for field_name, field_info in cls.model_fields.items():
            input_key = field_info.alias or field_name

            if input_key in converted_data:
                value = converted_data[input_key]
                target_type = field_info.annotation

                is_decimal_like = cls._is_decimal_like_annotation(target_type)
                is_float_value = isinstance(value, float)

                if is_decimal_like and is_float_value:
                    converted_data[input_key] = Decimal(str(value))
                elif isinstance(value, list):
                    list_item_type = None
                    origin = get_origin(target_type)
                    args = get_args(target_type)

                    if origin in (list, List) and args:
                        list_item_type = args[0]
                    elif origin is Union:  # Handle Optional[List[X]]
                        for arg in args:
                            if get_origin(arg) in (list, List) and get_args(arg):
                                list_item_type = get_args(arg)[0]
                                break

                    if list_item_type:
                        new_list = []
                        for item in value:
                            item_is_decimal_like = cls._is_decimal_like_annotation(list_item_type)
                            item_is_float_value = isinstance(item, float)

                            if item_is_decimal_like and item_is_float_value:
                                new_list.append(Decimal(str(item)))
                            elif isinstance(item, dict) and isinstance(list_item_type, type) and issubclass(list_item_type, BaseModel):
                                new_list.append(list_item_type._convert_floats_to_decimals(item))
                            else:
                                new_list.append(item)
                        converted_data[input_key] = new_list
                elif isinstance(value, dict) and isinstance(target_type, type) and issubclass(target_type, BaseModel):
                    converted_data[input_key] = target_type._convert_floats_to_decimals(value)

        return converted_data

    @classmethod
    def _is_decimal_like_annotation(cls, type_hint: Any) -> bool:
        """Checks if a type hint (or its contained types) is Decimal."""
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        if type_hint is Decimal:
            return True
        if origin is Union:  # Handles Optional[X] which is Union[X, None]
            return any(cls._is_decimal_like_annotation(arg) for arg in args)
        if origin is Annotated:
            return cls._is_decimal_like_annotation(args[0])
        # For List[Decimal], we check the item type
        if origin in (list, List) and args:
            return cls._is_decimal_like_annotation(args[0])
        # Pydantic's Json type is a special case, it wraps another type
        if str(origin) == "<class 'pydantic.types.Json'>" and args:
            return cls._is_decimal_like_annotation(args[0])
        return False


def parse_flexible_datetime(v: str | datetime) -> datetime:
    """Parse datetime from multiple formats using dateutil."""
    if v in {"NOW*()", "NOW()"}:
        return datetime.fromtimestamp(0, tz=UTC)

    if isinstance(v, str):
        parsed = parser.parse(v)
        if not isinstance(parsed, datetime):
            msg = f"Failed to parse '{v}' as datetime, got {type(parsed)}"
            raise TypeError(msg)
        return parsed
    return v


def validate_keccak256(v: str | HexBytes | bytes) -> str:
    """Validate and normalize Keccak256 hash format."""
    # Convert HexBytes/bytes to string
    if isinstance(v, HexBytes | bytes):
        v = v.hex()

    # Ensure string and add 0x prefix if missing
    if not isinstance(v, str):
        msg = f"Expected string or bytes, got {type(v)}"
        raise TypeError(msg)

    if not v.startswith("0x"):
        v = "0x" + v

    # Validate format: 0x followed by 64 hex characters
    if not re.match(r"^0x[a-fA-F0-9]{64}$", v):
        msg = f"Invalid Keccak256 hash format: {v}"
        raise ValueError(msg)

    return v


def validate_eth_address(v: str | HexBytes | bytes) -> str:
    """Validate and normalize Ethereum address format."""
    # Convert HexBytes/bytes to string
    if isinstance(v, HexBytes | bytes):
        v = v.hex()

    # Ensure string and add 0x prefix if missing
    if not isinstance(v, str):
        msg = f"Expected string or bytes, got {type(v)}"
        raise TypeError(msg)

    if not v.startswith("0x"):
        v = "0x" + v

    # Validate format: 0x followed by 40 hex characters
    if not re.match(r"^0x[a-fA-F0-9]{40}$", v, re.IGNORECASE):
        msg = f"Invalid Ethereum address format: {v}"
        raise ValueError(msg)

    return v


def hexbytes_to_str(v: Any) -> str:
    """Convert HexBytes to hex string with 0x prefix."""
    if isinstance(v, HexBytes):
        hex_str = v.hex()
        return hex_str if hex_str.startswith("0x") else f"0x{hex_str}"
    if isinstance(v, bytes):
        return "0x" + v.hex()
    if isinstance(v, str) and not v.startswith("0x"):
        return f"0x{v}"
    return v


def validate_keccak_or_padded(v: Any) -> str:
    """
    Validate Keccak256 or accept padded addresses (32 bytes with leading zeros).

    Some log topics are padded addresses, not proper Keccak256 hashes.
    """
    # First convert HexBytes/bytes to string with 0x prefix
    if isinstance(v, HexBytes | bytes):
        v = v.hex()

    # Ensure it's a string
    if not isinstance(v, str):
        msg = f"Expected string or bytes, got {type(v)}"
        raise TypeError(msg)

    # Add 0x prefix if missing
    if not v.startswith("0x"):
        v = "0x" + v

    # Accept 66 character hex strings (0x + 64 hex chars)
    if len(v) == 66 and all(c in "0123456789abcdefABCDEF" for c in v[2:]):
        return v

    msg = (
        f"Invalid hash format: expected 66 characters (0x + 64 hex), got {len(v)}: {v}"
    )
    raise ValueError(msg)


FlexibleDatetime = Annotated[datetime, BeforeValidator(parse_flexible_datetime)]
EthAddress = Annotated[str, AfterValidator(validate_eth_address)]
Keccak256 = Annotated[str, AfterValidator(validate_keccak256)]
HexString = Annotated[str, BeforeValidator(hexbytes_to_str)]
Keccak256OrPadded = Annotated[str, BeforeValidator(validate_keccak_or_padded)]
EmptyString = Annotated[str, Field(pattern=r"^$", description="An empty string")]


class TimeseriesPoint(Base):
    value: Decimal = Field(alias="p")
    timestamp: datetime = Field(alias="t")
