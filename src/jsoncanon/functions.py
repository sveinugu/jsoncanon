from jsoncanon.types import DecimalParts, FinalJson, JsonWithFinal


def float_to_es6_str(val: float, /) -> FinalJson:
    """Return a finite float as an RFC 8785 ECMAScript number token.

    Python's ``repr`` supplies the shortest round-tripping decimal
    selected by the equivalent of ECMAScript 6 §7.1.12.1 step 5's
    alternative implementation in Note 2. This function applies the
    fixed-versus- exponential notation rules required by RFC 8785 §3.2.2.3
    (rest of the algorithm in ECMAScript 6 §7.1.12.1): for example,
    ``1e-7`` becomes ``"1e-7"`` and ``1e-5`` becomes ``"0.00001"``. NaN
    and infinities are not permitted by RFC 8785.

    Returns:
        FinalJson: the canonical string representation of the float.
    """
    if val != val or val in (float('inf'), float('-inf')):
        raise ValueError('NaN and Infinity are not allowed by RFC 8785')
    elif val == 0:
        return FinalJson('0')  # also normalizes -0.0
    else:
        decimal_parts = _split_repr_into_decimal_parts(repr(val))
        out = _render_number_as_es6_tostring(decimal_parts)
        return FinalJson(out)


def _split_repr_into_decimal_parts(float_repr: str) -> DecimalParts:
    """Convert the ``repr`` of a nonzero, non-negative float to decimal parts.

    The result stores the significant digits without leading or trailing
    zeroes and the base-10 exponent of the first significant digit.
    """
    negative = float_repr.startswith('-')
    abs_float_repr = float_repr[1:] if negative else float_repr

    mantissa, separator, repr_exponent_str = abs_float_repr.partition('e')
    repr_exponent = int(repr_exponent_str) if separator else 0

    int_part, _, frac_part = mantissa.partition('.')
    all_digits = int_part + frac_part
    leading_zeroes = len(all_digits) - len(all_digits.lstrip('0'))
    digits = all_digits.strip('0')

    exponent = repr_exponent + len(int_part) - 1 - leading_zeroes

    return DecimalParts(negative, digits, exponent)


def _render_number_as_es6_tostring(number: DecimalParts) -> str:
    """Render normalized decimal parts using ECMAScript ``Number::toString``.

    ECMAScript uses fixed notation for values in ``[1e-6, 1e21)`` and
    exponential notation outside that range.
    """
    k = len(number.digits)
    n = number.exponent + 1

    if k <= n <= 21:
        abs_render = number.digits + '0' * (n - k)
    elif 0 < n <= 21:
        abs_render = number.digits[:n] + '.' + number.digits[n:]
    elif -6 < n <= 0:
        abs_render = '0.' + '0' * (-n) + number.digits
    else:
        e = n - 1
        exponent = 'e' + ('+' + str(e) if e >= 0 else str(e))

        if k == 1:
            significand = number.digits
        else:
            significand = number.digits[0] + '.' + number.digits[1:]

        abs_render = significand + exponent

    return '-' + abs_render if number.negative else abs_render


def int_to_str_if_too_large(i: int, /) -> int | str:
    if i > 2**53 or i < -(2**53):
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
