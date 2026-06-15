from decimal import Decimal
from rest_framework import serializers


USD_TO_BDT = Decimal("110")


class MoneyField(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 14)
        kwargs.setdefault("decimal_places", 2)
        super().__init__(**kwargs)

    def to_representation(self, value):
        if value is None:
            return None
        bdt_value = value * USD_TO_BDT
        return float(bdt_value)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return value / USD_TO_BDT


class MaskedCardField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 16)
        kwargs.setdefault("min_length", 16)
        kwargs.setdefault("write_only", False)
        super().__init__(**kwargs)

    def to_representation(self, value):
        if value is None:
            return None
        if len(value) < 4:
            return value
        return f"**** **** **** {value[-4:]}"

    def to_internal_value(self, data):
        cleaned = data.replace(" ", "").replace("-", "")
        if not cleaned.isdigit():
            raise serializers.ValidationError("Card number must contain only digits.")
        if len(cleaned) != 16:
            raise serializers.ValidationError(
                "Card number must be exactly 16 digits."
            )
        return cleaned


def validate_card_number(value):
    if not value.isdigit():
        raise serializers.ValidationError("Card number must be numeric.")
    if len(value) != 16:
        raise serializers.ValidationError(
            "Card number must be exactly 16 digits."
        )
