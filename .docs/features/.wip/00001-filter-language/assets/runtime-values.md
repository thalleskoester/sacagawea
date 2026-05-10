# Runtime Value Contract - V1

The interpreter may use an internal runtime value wrapper. If it does, the wrapper must expose:

| Field | Meaning |
|---|---|
| `type_name` | One of `String`, `Integer`, `Decimal`, `Boolean`, `List`, `Dictionary`, `Date`, `Time`, `DateTime`, `Null`. |
| `value` | Original Python value or derived temporal component value. |
| `path` | Current logical path when available for error context. |

Python values are classified in this order:

1. `None`
2. `bool`
3. `datetime.datetime`
4. `datetime.date`
5. `datetime.time`
6. `int`
7. finite `float`
8. `str`
9. `list`
10. `dict`

Unsupported values and non-finite floats raise `unsupported-runtime-value` when reached.

The integer values `0` and `1` are `Integer` values. Only Python `True` and `False` are `Boolean` values.
