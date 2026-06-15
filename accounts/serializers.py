from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Account
from .fields import MoneyField, MaskedCardField
from transactions.models import Transaction


class AccountBaseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField()
    account_number = serializers.CharField(max_length=20)
    card_number = MaskedCardField()
    balance = MoneyField()
    is_frozen = serializers.BooleanField(default=False)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_account_number(self, value):
        if not value.isalnum():
            raise serializers.ValidationError(
                "Account number must be alphanumeric."
            )
        return value

    def validate(self, data):
        if data.get("balance", 0) > 100000 and not data.get("is_frozen"):
            raise serializers.ValidationError(
                "High-balance accounts cannot be unfrozen."
            )
        return data

    def create(self, validated_data):
        return Account.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


class AccountDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    balance = MoneyField()

    class Meta:
        model = Account
        fields = "__all__"
        read_only_fields = ["user_email"]


class AccountListSerializer(serializers.ListSerializer):
    child = AccountSerializer()

    def create(self, validated_data):
        accounts = [Account(**item) for item in validated_data]
        return Account.objects.bulk_create(accounts)

    def update(self, instances, validated_data):
        instance_map = {inst.pk: inst for inst in instances}
        result = []
        for data in validated_data:
            pk = data.get("id")
            inst = instance_map.get(pk)
            if inst:
                for attr, value in data.items():
                    setattr(inst, attr, value)
                inst.save()
                result.append(inst)
        return result


class AccountBulkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"
        list_serializer_class = AccountListSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"


class TransactionDetailSerializer(serializers.ModelSerializer):
    account = AccountDetailSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = "__all__"


class NestedAccountWriteSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    account_number = serializers.CharField(max_length=20)
    card_number = serializers.CharField(max_length=16, validators=[])
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)

    def create(self, validated_data):
        return Account.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class TransactionNestedWriteSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["debit", "credit"])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)
    account = NestedAccountWriteSerializer()

    def validate(self, data):
        if data["type"] == "debit" and data["amount"] > data["account"]["balance"]:
            raise serializers.ValidationError("Insufficient balance for debit.")
        return data

    def create(self, validated_data):
        account_data = validated_data.pop("account")
        account = Account.objects.create(**account_data)
        transaction = Transaction.objects.create(
            account=account, **validated_data
        )
        return transaction

    def update(self, instance, validated_data):
        account_data = validated_data.pop("account", None)
        if account_data:
            acc = instance.account
            for attr, value in account_data.items():
                setattr(acc, attr, value)
            acc.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AccountStatementSerializer(serializers.ModelSerializer):
    transaction_count = serializers.SerializerMethodField()
    total_credited = serializers.SerializerMethodField()
    total_debited = serializers.SerializerMethodField()
    balance_in_taka = serializers.SerializerMethodField()
    last_active = serializers.SerializerMethodField()
    card_display = MaskedCardField(source="card_number", read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "account_number",
            "card_display",
            "balance",
            "balance_in_taka",
            "is_frozen",
            "transaction_count",
            "total_credited",
            "total_debited",
            "last_active",
            "created_at",
        ]

    def get_transaction_count(self, obj):
        return obj.transactions.count()

    def get_total_credited(self, obj):
        return sum(
            t.amount
            for t in obj.transactions.filter(type="credit")
        )

    def get_total_debited(self, obj):
        return sum(
            t.amount
            for t in obj.transactions.filter(type="debit")
        )

    def get_balance_in_taka(self, obj):
        from .fields import USD_TO_BDT
        return float(obj.balance * USD_TO_BDT)

    def get_last_active(self, obj):
        last_txn = obj.transactions.order_by("-timestamp").first()
        return last_txn.timestamp if last_txn else None


class AccountOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "account_number",
            "balance",
            "is_frozen",
            "created_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["status"] = "frozen" if instance.is_frozen else "active"
        data["balance_formatted"] = f"${instance.balance:.2f}"
        return data

    def to_internal_value(self, data):
        data = data.copy()
        if "status" in data:
            data["is_frozen"] = data.pop("status") == "frozen"
        return super().to_internal_value(data)
