from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class ActiveAccountManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Account.Status.ACTIVE)


class TransactionQuerySet(models.QuerySet):
    def completed(self):
        return self.filter(status=Transaction.Status.COMPLETED)

    def pending(self):
        return self.filter(status=Transaction.Status.PENDING)

    def failed(self):
        return self.filter(status=Transaction.Status.FAILED)

    def today(self):
        return self.filter(created_at__date=date.today())

    def by_type(self, txn_type):
        return self.filter(transaction_type=txn_type)

    def outgoing(self):
        return self.filter(direction=Transaction.Direction.OUTGOING)

    def incoming(self):
        return self.filter(direction=Transaction.Direction.INCOMING)


class TransactionManager(models.Manager):
    def get_queryset(self):
        return TransactionQuerySet(self.model, using=self._db)

    def completed(self):
        return self.get_queryset().completed()

    def pending(self):
        return self.get_queryset().pending()

    def today(self):
        return self.get_queryset().today()


class UserProfile(models.Model):
    class KYCStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True)
    kyc_status = models.CharField(
        max_length=20, choices=KYCStatus.choices, default=KYCStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fintech_user_profile"

    def __str__(self):
        return f"{self.user.username} - {self.get_kyc_status_display()}"


class Account(models.Model):
    class Type(models.TextChoices):
        SAVINGS = "savings", "Savings"
        CHECKING = "checking", "Checking"
        CREDIT = "credit", "Credit"
        INVESTMENT = "investment", "Investment"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FROZEN = "frozen", "Frozen"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    account_number = models.CharField(max_length=20, unique=True, db_index=True)
    account_type = models.CharField(max_length=20, choices=Type.choices)
    currency = models.CharField(max_length=3, default="BDT")
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    objects = models.Manager()
    active_objects = ActiveAccountManager()

    class Meta:
        db_table = "fintech_account"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "account_type"],
                name="unique_user_account_type",
                condition=models.Q(status="active"),
            )
        ]
        indexes = [
            models.Index(fields=["status", "account_type"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.account_number} ({self.get_account_type_display()})"


class Merchant(models.Model):
    class Category(models.TextChoices):
        RETAIL = "retail", "Retail"
        FOOD = "food", "Food & Dining"
        TRAVEL = "travel", "Travel"
        TECH = "tech", "Technology"
        HEALTHCARE = "healthcare", "Healthcare"
        ENTERTAINMENT = "entertainment", "Entertainment"
        UTILITIES = "utilities", "Utilities"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TERMINATED = "terminated", "Terminated"

    name = models.CharField(max_length=255)
    merchant_code = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=Category.choices)
    country = models.CharField(max_length=100, default="BD")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fintech_merchant"
        indexes = [
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Transaction(models.Model):
    class Direction(models.TextChoices):
        INCOMING = "incoming", "Incoming"
        OUTGOING = "outgoing", "Outgoing"

    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        TRANSFER = "transfer", "Transfer"
        PAYMENT = "payment", "Payment"
        REFUND = "refund", "Refund"
        FEE = "fee", "Fee"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions"
    )
    destination_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_transactions",
    )
    direction = models.CharField(
        max_length=20, choices=Direction.choices, default=Direction.OUTGOING
    )
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    currency = models.CharField(max_length=3, default="BDT")
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionManager()

    class Meta:
        db_table = "fintech_transaction"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=Decimal("0.00")),
                name="transaction_amount_positive",
            ),
        ]
        indexes = [
            models.Index(fields=["account", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["transaction_type", "status"]),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} ${self.amount} - {self.get_status_display()}"


class Card(models.Model):
    class Type(models.TextChoices):
        DEBIT = "debit", "Debit"
        CREDIT = "credit", "Credit"
        PREPAID = "prepaid", "Prepaid"

    class Network(models.TextChoices):
        VISA = "visa", "Visa"
        MASTERCARD = "mastercard", "Mastercard"
        AMEX = "amex", "American Express"
        DISCOVER = "discover", "Discover"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        BLOCKED = "blocked", "Blocked"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cards")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="cards")
    card_number = models.CharField(max_length=16, unique=True, db_index=True)
    card_type = models.CharField(max_length=20, choices=Type.choices)
    card_network = models.CharField(max_length=20, choices=Network.choices)
    expiry_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    expiry_year = models.IntegerField()
    cvv = models.CharField(max_length=4)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fintech_card"
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["card_network", "card_type"]),
        ]

    def __str__(self):
        return f"{self.get_card_network_display()} ****{self.card_number[-4:]}"
