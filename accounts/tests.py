from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Account
from .serializers import (
    AccountBaseSerializer,
    AccountDetailSerializer,
    AccountBulkSerializer,
    AccountStatementSerializer,
    AccountOverrideSerializer,
    TransactionNestedWriteSerializer,
    TransactionDetailSerializer,
)
from .fields import MoneyField, MaskedCardField, USD_TO_BDT
from transactions.models import Transaction


class CustomFieldTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "pass")

    def test_moneyfield_representation(self):
        field = MoneyField()
        result = field.to_representation(Decimal("100.00"))
        expected = float(100 * USD_TO_BDT)
        self.assertIsInstance(result, float)
        self.assertAlmostEqual(result, expected, places=2)

    def test_masked_card_field_representation(self):
        field = MaskedCardField()
        result = field.to_representation("1234567890123456")
        self.assertEqual(result, "**** **** **** 3456")

    def test_masked_card_field_invalid_length(self):
        field = MaskedCardField()
        with self.assertRaises(serializers.ValidationError):
            field.run_validation("1234")

    def test_masked_card_field_valid(self):
        field = MaskedCardField()
        result = field.run_validation("1111222233334444")
        self.assertEqual(result, "1111222233334444")


class AccountBaseSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "alice@test.com", "pass")

    def test_base_serializer_create(self):
        data = {
            "user_id": self.user.id,
            "account_number": "ACC001",
            "card_number": "1111222233334444",
            "balance": 500.00,
            "is_frozen": False,
        }
        serializer = AccountBaseSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        account = serializer.save()
        self.assertEqual(account.account_number, "ACC001")
        self.assertEqual(account.user_id, self.user.id)

    def test_base_serializer_field_validation(self):
        data = {
            "user_id": self.user.id,
            "account_number": "ACC@123!",
            "card_number": "1111222233334444",
            "balance": 100.00,
            "is_frozen": False,
        }
        serializer = AccountBaseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("account_number", serializer.errors)

    def test_base_serializer_missing_required_field(self):
        data = {
            "account_number": "ACC002",
            "card_number": "1111222233334444",
            "balance": 200.00,
            "is_frozen": False,
        }
        serializer = AccountBaseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_id", serializer.errors)


class AccountDetailSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("bob", "bob@test.com", "pass")

    def test_user_email_in_detail(self):
        account = Account.objects.create(
            user=self.user, account_number="DET001",
            card_number="9999888877776666", balance=Decimal("250.00"),
        )
        serializer = AccountDetailSerializer(account)
        self.assertEqual(serializer.data["user_email"], "bob@test.com")


class AccountOverrideSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("carol", "carol@test.com", "pass")
        self.account = Account.objects.create(
            user=self.user, account_number="OVR001",
            card_number="1111222233334444", balance=Decimal("100.00"),
            is_frozen=True,
        )

    def test_override_representation(self):
        serializer = AccountOverrideSerializer(self.account)
        data = serializer.data
        self.assertEqual(data["status"], "frozen")
        self.assertIn("balance_formatted", data)


class AccountStatementSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("dave", "dave@test.com", "pass")
        self.account = Account.objects.create(
            user=self.user, account_number="STM001",
            card_number="1111222233334444", balance=Decimal("1000.00"),
        )
        Transaction.objects.create(
            account=self.account, amount=Decimal("200.00"),
            type="credit", description="deposit",
        )
        Transaction.objects.create(
            account=self.account, amount=Decimal("50.00"),
            type="debit", description="withdraw",
        )

    def test_statement_computed_fields(self):
        serializer = AccountStatementSerializer(self.account)
        data = serializer.data
        self.assertEqual(data["transaction_count"], 2)
        self.assertEqual(float(data["total_credited"]), 200.00)
        self.assertEqual(float(data["total_debited"]), 50.00)

    def test_statement_correct_count(self):
        serializer = AccountStatementSerializer(self.account)
        data = serializer.data
        self.assertEqual(data["transaction_count"], 2)


class TransactionNestedWriteSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("eve", "eve@test.com", "pass")

    def test_nested_create_transaction(self):
        data = {
            "type": "credit",
            "amount": "500.00",
            "description": "opening deposit",
            "account": {
                "user_id": self.user.id,
                "account_number": "NST001",
                "card_number": "1111222233334444",
                "balance": "500.00",
            },
        }
        serializer = TransactionNestedWriteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        transaction = serializer.save()
        self.assertIsNotNone(transaction.id)
        self.assertEqual(transaction.account.account_number, "NST001")

    def test_nested_create_missing_field(self):
        data = {
            "type": "credit",
            "amount": "300.00",
            "description": "deposit",
            "account": {
                "user_id": self.user.id,
                "account_number": "NST002",
                "balance": "300.00",
            },
        }
        serializer = TransactionNestedWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("account", serializer.errors)


class TransactionDetailSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("frank", "frank@test.com", "pass")
        self.account = Account.objects.create(
            user=self.user, account_number="TDT001",
            card_number="1111222233334444", balance=Decimal("100.00"),
        )
        self.transaction = Transaction.objects.create(
            account=self.account, amount=Decimal("50.00"),
            type="debit", description="payment",
        )

    def test_nested_account_detail_in_transaction(self):
        serializer = TransactionDetailSerializer(self.transaction)
        self.assertIn("account", serializer.data)
        self.assertIn("user_email", serializer.data["account"])


class AccountBulkSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("grace", "grace@test.com", "pass")

    def test_bulk_create(self):
        data = [
            {
                "user": self.user.id,
                "account_number": "BLK001",
                "card_number": "1111222233334444",
                "balance": "100.00",
                "is_frozen": False,
            },
            {
                "user": self.user.id,
                "account_number": "BLK002",
                "card_number": "5555666677778888",
                "balance": "200.00",
                "is_frozen": False,
            },
        ]
        serializer = AccountBulkSerializer(data=data, many=True)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        accounts = serializer.save()
        self.assertEqual(len(accounts), 2)
        self.assertEqual(Account.objects.count(), 2)
