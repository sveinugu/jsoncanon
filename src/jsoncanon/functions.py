import re
from jsoncanon.types import JsonWithFinal


def float_to_es6_str(f: float) -> str:
    """Serialize a finite float as ECMAScript Number::toString (RFC 8785
    §3.2.2.3). ``repr`` already yields the shortest round-tripping decimal;
    this only re-applies the ES6 positional-vs-exponential rules to it, so
    e.g. 1e-7 -> "1e-7" (not "1e-07") and 1e-5 -> "0.00001" (not "1e-05")."""
    if f != f or f in (float('inf'), float('-inf')):
        raise ValueError('NaN and Infinity are not allowed by RFC 8785')
    if f == 0:
        return '0'  # also normalizes -0.0
    neg = f < 0
    digits, exp = _significand_and_exponent(repr(abs(f)))
    out = _es6_positional_or_exponential(digits, exp)
    return '-' + out if neg else out


def _significand_and_exponent(rep: str) -> Tuple[str, int]:
    """Split ``repr(f)`` into its significant digits (trailing zeros stripped)
    and the base-10 exponent of the leading digit."""
    if 'e' in rep or 'E' in rep:
        mantissa, exponent = re.split('[eE]', rep)
        int_part, _, frac_part = mantissa.partition('.')
        digits = int_part + frac_part
        exp_val = int(exponent)
    else:
        int_part, _, frac_part = rep.partition('.')
        all_digits = int_part + frac_part
        first = next(i for i, c in enumerate(all_digits) if c in '123456789')
        exp_val = len(int_part) - 1 - first
        digits = all_digits[first:]
    return digits.rstrip('0') or '0', exp_val


def _es6_positional_or_exponential(digits: str, exp_val: int) -> str:
    """Render a significand and exponent using the ECMAScript
    Number::toString positional-vs-exponential rules (RFC 8785 §3.2.2.3)."""
    k = len(digits)
    n = exp_val + 1
    if k <= n <= 21:
        return digits + '0' * (n - k)
    if 0 < n <= 21:
        return digits[:n] + '.' + digits[n:]
    if -6 < n <= 0:
        return '0.' + '0' * (-n) + digits
    e = n - 1
    exp_str = ('+' + str(e)) if e >= 0 else str(e)
    return (digits if k == 1 else digits[0] + '.' + digits[1:]) + 'e' + exp_str


def int_to_str_if_too_large(i: int, /) -> int | str:
    if i >= 2**63 or i <= -(2**63):
        return str(i)
    else:
        return i


def float_to_int_if_whole_and_not_large_exp(f: float, /) -> int | float:
    if f.is_integer() and abs(f) < 1e21:
        return int(f)
    else:
        return f


def to_utf16_tuple(any_str: str) -> tuple[int, ...]:
    utf_16_bytes = any_str.encode('utf-16-be')
    return tuple(
        int.from_bytes(utf_16_bytes[i : i + 2], 'big') for i in range(0, len(utf_16_bytes), 2)
    )


def _key_to_utf16_tuple(keyval: tuple[str, JsonWithFinal]) -> tuple[int, ...]:
    key, _val = keyval
    return to_utf16_tuple(key)


def dict_to_sorted_by_utf16_tuple(d: dict[str, JsonWithFinal], /) -> dict[str, JsonWithFinal]:
    return dict(sorted(d.items(), key=_key_to_utf16_tuple))
