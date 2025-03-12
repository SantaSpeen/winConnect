import struct


class SimpleConvertor:

    @classmethod
    def to_kb(cls, value: int) -> int:
        return value * 1024

    @classmethod
    def to_mb(cls, value: int) -> int:
        return cls.to_kb(value) * 1024

    @classmethod
    def to_gb(cls, value: int) -> int:
        return cls.to_mb(value) * 1024

    @classmethod
    def struct_range(cls, format_str):
        """Return min and max value for struct format"""
        size = struct.calcsize(format_str)
        fmt = format_str.lstrip("><=!")
        signed = fmt[0].islower()
        bit_size = size * 8
        if signed:
            min_value = -(1 << (bit_size - 1))  # -(2^(N-1))
            max_value = (1 << (bit_size - 1)) - 1  # 2^(N-1) - 1
        else:
            min_value = 0
            max_value = (1 << bit_size) - 1  # 2^N - 1

        return min_value, max_value

