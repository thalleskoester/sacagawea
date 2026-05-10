"""Deterministic benchmark datasets for sacagawea."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Final

DATASET_SIZES: Final[dict[str, int]] = {
    "small": 100,
    "medium": 10_000,
    "large": 100_000,
}

QUERY_NAMES: Final[tuple[str, ...]] = (
    "scalar_eq",
    "numeric_and",
    "many_args",
    "deep_expression",
    "deep_path_8",
    "deep_path_32",
    "query_fanout",
    "query_nested",
    "scalar_list_regex",
    "regex_simple",
    "regex_complex",
    "short_circuit_and",
    "short_circuit_or",
    "temporal_component",
)


@dataclass(frozen=True, slots=True)
class BenchmarkDataset:
    """A generated dataset and its expected match counts."""

    name: str
    records: list[dict]
    expected_counts: dict[str, int]


def build_dataset(name: str) -> BenchmarkDataset:
    """Build one named deterministic dataset."""
    if name not in DATASET_SIZES:
        choices = ", ".join(sorted(DATASET_SIZES))
        message = f"Unknown benchmark dataset {name!r}; expected one of: {choices}"
        raise ValueError(message)

    size = DATASET_SIZES[name]
    records = [_build_record(index) for index in range(size)]
    expected_counts = {query_name: _count_expected(query_name, size) for query_name in QUERY_NAMES}
    return BenchmarkDataset(name=name, records=records, expected_counts=expected_counts)


def _build_record(index: int) -> dict:
    first_name = "john" if index % 10 == 0 else f"user-{index:06d}"
    email_domain = "example.com" if index % 3 == 0 else "other.test"
    tracking_code = f"ORD-{index % 10_000:04d}-alpha-north" if index % 4 == 0 else f"bad-{index % 10_000:04d}-code"
    active = index % 2 == 0
    return {
        "record_id": index,
        "first_name": first_name,
        "age": 18 + (index % 70),
        "balance": (index % 2_000) / 10,
        "score": index % 1_000,
        "country": "BR" if index % 5 == 0 else "US",
        "is_active": active,
        "deleted_at": None if index % 17 == 0 else f"2026-05-{(index % 28) + 1:02d}",
        "email": f"{first_name}.{index:06d}@{email_domain}",
        "tracking_code": tracking_code,
        "customer": {
            "address": {
                "city": "Paris" if index % 11 == 0 else "Lyon",
                "postal_code": f"{75_000 + (index % 1_000)}",
            }
        },
        "deep": _deep_dictionary(30, index),
        "roles": _roles(index),
        "teams": _teams(index),
        "last_ips": _last_ips(index),
        "created_at": dt.datetime(2026 if index % 13 == 0 else 2025, 5, 10, 12, 0, tzinfo=dt.UTC),
    }


def _deep_dictionary(depth: int, index: int) -> dict:
    leaf_value = "target" if index % 7 == 0 else "miss"
    value: dict = {"value": leaf_value}
    for level in range(depth, 0, -1):
        value = {f"level_{level:02d}": value, "value": leaf_value}
    return value


def _roles(index: int) -> list[dict[str, str]]:
    roles = [{"name": "user"}, {"name": "editor"}]
    if index % 5 == 0:
        roles.append({"name": "root"})
    return roles


def _teams(index: int) -> list[dict[str, object]]:
    return [
        {
            "name": "platform",
            "members": [
                {
                    "active": index % 6 == 0,
                    "email": f"member.{index:06d}@example.com" if index % 6 == 0 else f"member.{index:06d}@other.test",
                },
                {"active": False, "email": f"inactive.{index:06d}@example.com"},
            ],
        },
        {
            "name": "support",
            "members": [{"active": False, "email": f"support.{index:06d}@other.test"}],
        },
    ]


def _last_ips(index: int) -> list[str]:
    ips = [f"172.16.{index % 255}.{(index * 7) % 255}", f"192.168.{index % 255}.{(index * 11) % 255}"]
    if index % 8 == 0:
        ips.append(f"10.238.115.{index % 255}")
    return ips


def _count_expected(query_name: str, size: int) -> int:
    divisors = {
        "scalar_eq": 10,
        "deep_path_8": 7,
        "deep_path_32": 7,
        "query_fanout": 5,
        "query_nested": 6,
        "scalar_list_regex": 8,
        "regex_simple": 3,
        "regex_complex": 4,
        "temporal_component": 13,
    }
    if query_name in {"numeric_and", "many_args", "deep_expression"}:
        return _count_multiples(size, 2)
    if query_name == "short_circuit_and":
        return 0
    if query_name == "short_circuit_or":
        return size
    return _count_multiples(size, divisors[query_name])


def _count_multiples(size: int, divisor: int) -> int:
    return 0 if size <= 0 else ((size - 1) // divisor) + 1
