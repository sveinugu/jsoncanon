from typing import NoReturn

from jsoncanon.functions import float_to_es6_str, is_es6_safe_integer, to_utf16_tuple


class CanonicalJsonValidator:
    def __init__(self, data: object) -> None:
        if not isinstance(data, bytes):
            raise TypeError(f'Data must be bytes, not {type(data).__name__}')

        self._data: bytes = data
        self._index = 0

    def validate(self) -> None:
        self._parse_value()
        if self._index != len(self._data):
            self._fail('unexpected trailing data')

    def _parse_value(self) -> None:
        if self._index == len(self._data):
            self._fail('expected a value')

        byte = self._data[self._index]
        if byte == ord('{'):
            self._parse_object()
        elif byte == ord('['):
            self._parse_array()
        elif byte == ord('"'):
            self._parse_string()
        elif byte == ord('t'):
            self._parse_literal(b'true')
        elif byte == ord('f'):
            self._parse_literal(b'false')
        elif byte == ord('n'):
            self._parse_literal(b'null')
        elif byte == ord('-') or ord('0') <= byte <= ord('9'):
            self._parse_number()
        else:
            self._fail('expected a value')

    def _parse_object(self) -> None:
        self._index += 1
        if self._consume(ord('}')):
            return

        previous_key: tuple[int, ...] | None = None
        while True:
            if self._peek() != ord('"'):
                self._fail('object key must be a string')
            key = self._parse_string()
            key_utf16 = to_utf16_tuple(key)
            if previous_key is not None and key_utf16 <= previous_key:
                self._fail('object keys are not in strictly increasing UTF-16 order')
            previous_key = key_utf16

            self._expect(ord(':'), 'expected colon after object key')
            self._parse_value()
            if self._consume(ord('}')):
                return
            self._expect(ord(','), 'expected comma after object member')

    def _parse_array(self) -> None:
        self._index += 1
        if self._consume(ord(']')):
            return

        while True:
            self._parse_value()
            if self._consume(ord(']')):
                return
            self._expect(ord(','), 'expected comma after array item')

    def _parse_string(self) -> str:
        self._index += 1
        decoded = bytearray()
        while self._index < len(self._data):
            byte = self._data[self._index]
            self._index += 1

            if byte == ord('"'):
                try:
                    return decoded.decode('utf-8')
                except UnicodeDecodeError:
                    self._fail('string is not valid UTF-8')
            if byte < 0x20:
                self._fail('unescaped control character in string')
            if byte != ord('\\'):
                decoded.append(byte)
                continue
            self._parse_escape(decoded)

        self._fail('unterminated string')

    def _parse_escape(self, decoded: bytearray) -> None:
        if self._index == len(self._data):
            self._fail('unterminated escape sequence')
        escape = self._data[self._index]
        self._index += 1
        escapes = {
            ord('"'): ord('"'),
            ord('\\'): ord('\\'),
            ord('b'): 0x08,
            ord('t'): 0x09,
            ord('n'): 0x0A,
            ord('f'): 0x0C,
            ord('r'): 0x0D,
        }
        if escape == ord('u'):
            self._parse_canonical_unicode_escape(decoded)
        elif escape in escapes:
            decoded.append(escapes[escape])
        else:
            self._fail('non-canonical string escape')

    def _parse_canonical_unicode_escape(self, decoded: bytearray) -> None:
        end = self._index + 4
        hex_digits = self._data[self._index : end]
        if len(hex_digits) != 4 or any(digit not in b'0123456789abcdef' for digit in hex_digits):
            self._fail('unicode escape must use four lowercase hexadecimal digits')
        self._index = end
        value = int(hex_digits, 16)
        if value in (0x08, 0x09, 0x0A, 0x0C, 0x0D) or value >= 0x20:
            self._fail('non-canonical unicode escape')
        decoded.append(value)

    def _parse_number(self) -> None:
        start = self._index
        if self._consume(ord('-')) and self._peek() is None:
            self._fail('invalid number')

        self._parse_integer_part()
        is_integer = self._parse_fraction_and_exponent()

        token = self._data[start : self._index].decode('ascii')
        if is_integer and token != '-0' and is_es6_safe_integer(int(token)):
            return

        try:
            canonical_token = float_to_es6_str(float(token))
        except ValueError:
            self._fail('number is outside the supported canonical range')
        if token != canonical_token:
            self._fail('non-canonical number')

    def _parse_integer_part(self) -> None:
        if self._consume(ord('0')):
            return
        if self._peek_is_digit():
            self._consume_digits()
            return
        self._fail('invalid number')

    def _parse_fraction_and_exponent(self) -> bool:
        is_integer = True
        if self._consume(ord('.')):
            is_integer = False
            if not self._peek_is_digit():
                self._fail('invalid fractional number')
            self._consume_digits()

        if self._peek() in (ord('e'), ord('E')):
            is_integer = False
            self._index += 1
            if not self._consume(ord('+')):
                self._consume(ord('-'))
            if not self._peek_is_digit():
                self._fail('invalid exponent')
            self._consume_digits()
        return is_integer

    def _parse_literal(self, literal: bytes) -> None:
        if self._data[self._index : self._index + len(literal)] != literal:
            self._fail(f'expected {literal.decode()!r}')
        self._index += len(literal)

    def _consume(self, byte: int) -> bool:
        if self._peek() == byte:
            self._index += 1
            return True
        return False

    def _consume_digits(self) -> None:
        while self._peek_is_digit():
            self._index += 1

    def _expect(self, byte: int, message: str) -> None:
        if not self._consume(byte):
            self._fail(message)

    def _peek(self) -> int | None:
        if self._index == len(self._data):
            return None
        return self._data[self._index]

    def _peek_is_digit(self) -> bool:
        byte = self._peek()
        return byte is not None and ord('0') <= byte <= ord('9')

    def _fail(self, message: str) -> NoReturn:
        raise ValueError(f'Data is not canonical JSON at byte {self._index}: {message}')
