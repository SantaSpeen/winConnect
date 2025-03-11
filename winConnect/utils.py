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
