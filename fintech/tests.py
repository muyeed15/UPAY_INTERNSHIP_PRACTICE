from decimal import Decimal

from django.test import TestCase
from django.db.models import (
    Count,
    Sum,
    F,
    Q,
    Case,
    When,
    Value,
    CharField,
    Subquery,
    OuterRef,
)
from django.contrib.auth.models import User
from .models import Account, Transaction, Card, Merchant, UserProfile


class ORMConceptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user("testuser", "test@example.com", "pass")
        UserProfile.objects.create(user=user, phone="555-0000", kyc_status="verified")

        merchant = Merchant.objects.create(
            name="TestMart", merchant_code="TM01", category="retail", country="BD"
        )

        cls.checking = Account.objects.create(
            user=user,
            account_number="CHK10000001",
            account_type="checking",
            balance=Decimal("5000.00"),
        )
        cls.savings = Account.objects.create(
            user=user,
            account_number="SAV10000001",
            account_type="savings",
            balance=Decimal("15000.00"),
        )

        for i in range(5):
            Transaction.objects.create(
                account=cls.checking,
                transaction_type="payment",
                amount=Decimal(f"{i+1}0.00"),
                status="completed",
                direction="outgoing",
                merchant=merchant,
            )
        for i in range(3):
            Transaction.objects.create(
                account=cls.checking,
                transaction_type="deposit",
                amount=Decimal(f"{i+1}00.00"),
                status="completed",
                direction="incoming",
            )
        Transaction.objects.create(
            account=cls.checking,
            transaction_type="withdrawal",
            amount=Decimal("9999.00"),
            status="failed",
            direction="outgoing",
        )

        Card.objects.create(
            user=user,
            account=cls.checking,
            card_number="4111111111111111",
            card_type="debit",
            card_network="visa",
            expiry_month=12,
            expiry_year=2029,
            cvv="123",
        )

    def test_select_related(self):
        with self.assertNumQueries(1):
            for a in Account.objects.select_related("user").filter(status="active"):
                _ = a.user.username

    def test_prefetch_related(self):
        with self.assertNumQueries(2):
            for a in Account.objects.prefetch_related("transactions").all():
                _ = list(a.transactions.all())

    def test_F_expression(self):
        Account.objects.filter(pk=self.checking.pk).update(
            balance=F("balance") + Decimal("100.00")
        )
        self.checking.refresh_from_db()
        self.assertEqual(self.checking.balance, Decimal("5100.00"))

    def test_Q_objects(self):
        results = Transaction.objects.filter(
            Q(amount__gt=Decimal("100.00")) | Q(transaction_type="payment")
        )
        self.assertGreaterEqual(results.count(), 5)

    def test_annotation(self):
        results = Account.objects.annotate(txn_count=Count("transactions"))
        self.assertEqual(results.get(pk=self.checking.pk).txn_count, 9)

    def test_aggregation(self):
        stats = Transaction.objects.filter(
            account=self.checking, status="completed"
        ).aggregate(total=Sum("amount"), count=Count("id"))
        self.assertEqual(stats["count"], 8)
        self.assertEqual(stats["total"], Decimal("750.00"))

    def test_conditional_expression(self):
        result = (
            Transaction.objects.annotate(
                size=Case(
                    When(amount__lt=Decimal("50.00"), then=Value("small")),
                    When(amount__lt=Decimal("150.00"), then=Value("medium")),
                    default=Value("large"),
                    output_field=CharField(),
                )
            )
            .filter(account=self.checking)
            .first()
        )
        self.assertIn(result.size, ["small", "medium", "large"])

    def test_subquery(self):
        latest_txn = (
            Transaction.objects.filter(account=OuterRef("pk"))
            .order_by("-created_at")
            .values("amount")[:1]
        )

        acct = Account.objects.annotate(last_amount=Subquery(latest_txn)).get(
            pk=self.checking.pk
        )
        self.assertIsNotNone(acct.last_amount)

    def test_custom_manager(self):
        active = Account.active_objects.all()
        self.assertGreaterEqual(active.count(), 1)

    def test_queryset_methods(self):
        completed = Transaction.objects.completed()
        self.assertGreaterEqual(completed.count(), 8)
        today_txns = Transaction.objects.today()
        self.assertGreaterEqual(today_txns.count(), 0)
