# Temporal Format Contract - V1

Temporal runtime values come from Python records. The filter language does not have date, time, or datetime literals in v1.

## Date

Date comparison methods accept ISO 8601 strings formatted as:

```text
YYYY-MM-DD
```

The runtime receiver is a Python `datetime.date` that is not a `datetime.datetime`.

## Time

Time comparison methods accept exactly these timezone-aware ISO 8601 forms:

```text
HH:MM:SSZ
HH:MM:SS+HH:MM
HH:MM:SS-HH:MM
```

Clock fields must be in valid ranges. Fractional seconds, lowercase `z`, compact offsets, offset seconds, named time zones, and omitted seconds are not accepted in v1.

The runtime receiver and the string argument must both be timezone-aware. Time comparison normalizes offsets into UTC time-of-day and ignores date rollover.

## DateTime

DateTime comparison methods accept exactly these timezone-aware ISO 8601 forms:

```text
YYYY-MM-DDTHH:MM:SSZ
YYYY-MM-DDTHH:MM:SS+HH:MM
YYYY-MM-DDTHH:MM:SS-HH:MM
```

Date and clock fields must be in valid ranges. Fractional seconds, lowercase `z`, a space separator instead of `T`, compact offsets, offset seconds, named time zones, and omitted seconds are not accepted in v1.

The runtime receiver and the string argument must both be timezone-aware. DateTime comparison normalizes offsets and compares the represented instant.

## Errors

Unparsable or wrong-format temporal strings raise `invalid-temporal-string`.

Direct `Time` or `DateTime` comparison with non-timezone-aware runtime values or string arguments raises `temporal-awareness-mismatch`.
