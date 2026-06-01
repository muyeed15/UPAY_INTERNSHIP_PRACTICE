from datetime import date, timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    Sum,
    Avg,
    F,
    Q,
    Case,
    When,
    Value,
    CharField,
    DecimalField,
    Subquery,
    OuterRef,
    Exists,
    Func,
    Window,
    Prefetch,
)
from django.db.models.functions import Concat, TruncMonth
from django.contrib.auth.models import User
from fintech.models import Account, Transaction, Card, Merchant

# Query 1: Use select_related to join User data with Account.
# Instead of making one query per account to get the user,
# select_related does a SQL JOIN so everything comes in one query.
active_accounts = Account.objects.select_related("user").filter(status="active")

# Query 2: Use annotate to add a calculated field to each User.
# Here we count how many accounts each user has.
users_with_account_count = User.objects.annotate(account_count=Count("accounts"))

# Query 3: Group accounts by type and calculate stats for each group.
# We get the total balance, average balance, and count per account type.
balance_by_type = Account.objects.values("account_type").annotate(
    total_balance=Sum("balance"), avg_balance=Avg("balance"), count=Count("id")
)

# Query 4: Use F() to update a field based on its current value.
# This gives a 2 percent interest bonus to all savings accounts.
# F() prevents race conditions by doing the math in the database.
Account.objects.filter(account_type="savings").update(
    balance=F("balance") * Decimal("1.02")
)

# Query 5: Use Q() to build complex OR conditions in a filter.
# Get transactions that are either completed and above $200,
# or failed and created in the last 7 days.
recent_or_large_txns = Transaction.objects.filter(
    Q(status="completed", amount__gt=Decimal("200.00"))
    | Q(status="failed", created_at__gte=date.today() - timedelta(days=7))
)

# Query 6: Use Case and When to add a category label to each transaction.
# This is like an if-else statement inside the database.
# Small = under $50, Medium = under $200, Large = under $1000, Whale = $1000+
txns_with_tier = Transaction.objects.annotate(
    tier=Case(
        When(amount__lt=Decimal("50.00"), then=Value("small")),
        When(amount__lt=Decimal("200.00"), then=Value("medium")),
        When(amount__lt=Decimal("1000.00"), then=Value("large")),
        default=Value("whale"),
        output_field=CharField(),
    )
)

# Query 7: Use a Subquery to pull data from one model into another.
# This subquery gets the most recent transaction amount for each account.
# OuterRef("pk") refers to the Account's primary key from the outer query.
latest_txn_subq = (
    Transaction.objects.filter(account=OuterRef("pk"))
    .order_by("-created_at")
    .values("amount")[:1]
)

# Query 8: Annotate each account with its last transaction amount.
# The Subquery runs once, not once per account.
accounts_with_latest_txn = Account.objects.annotate(
    last_txn_amount=Subquery(latest_txn_subq, output_field=DecimalField())
)

# Query 9: Use Exists to filter based on whether a related row exists.
# Find users who have at least one payment transaction.
# Exists is faster than Count because it stops at the first match.
high_confidence_users = User.objects.annotate(
    has_payment=Exists(
        Transaction.objects.filter(
            account__user=OuterRef("pk"), transaction_type="payment"
        )
    )
).filter(has_payment=True)

# Query 10: Use Prefetch to fetch related objects in a custom way.
# Here we get all users and preload only completed transactions.
# The to_attr puts results in a list instead of a queryset.
active_txn_prefetch = Prefetch(
    "accounts__transactions",
    queryset=Transaction.objects.filter(status="completed"),
    to_attr="completed_txns",
)
users_with_completed_txns = User.objects.prefetch_related(active_txn_prefetch)

# Query 11: Use Window to calculate a running total without grouping.
# For each transaction, it sums all previous transactions in the same account.
# The partition_by splits the data by account like a GROUP BY inside the window.
txns_with_running_total = Transaction.objects.annotate(
    running_total=Window(
        expression=Sum("amount"),
        partition_by=[F("account")],
        order_by=F("created_at").asc(),
    )
)

# Query 12: Use annotate with the filter argument to count conditionally.
# For each merchant we get total transactions, completed ones, and revenue.
merchant_stats = Merchant.objects.annotate(
    total_txns=Count("transactions"),
    completed_txns=Count("transactions", filter=Q(transactions__status="completed")),
    total_revenue=Sum(
        "transactions__amount", filter=Q(transactions__status="completed")
    ),
)

# Query 13: Use TruncMonth to group transactions by month.
# First we filter to only completed ones, then truncate the date to month,
# then group by month and calculate totals.
monthly_volume = (
    Transaction.objects.filter(status="completed")
    .annotate(month=TruncMonth("created_at"))
    .values("month")
    .annotate(total=Sum("amount"), count=Count("id"))
    .order_by("month")
)

# Query 14: Use ~Q (not Q) to exclude records that match a condition.
# Find active accounts with verified KYC, but exclude checking accounts
# that have a negative balance.
healthy_accounts = Account.objects.filter(
    Q(status="active"),
    ~Q(account_type="checking", balance__lt=Decimal("0.00")),
    user__profile__kyc_status="verified",
)

# Query 15: Use Concat and Func to create a custom display string.
# This builds a masked card number like "Visa ****1111 (debit)".
# Func calls the SQL SUBSTR function to get the last 4 digits.
card_display = Card.objects.annotate(
    display_name=Concat(
        F("card_network"),
        Value(" ****"),
        Func(F("card_number"), Value(4), function="SUBSTR"),
        Value(" ("),
        F("card_type"),
        Value(")"),
        output_field=CharField(),
    )
)

# Query 16: Bulk update using F() to freeze accounts with negative balance.
Account.objects.filter(balance__lt=0).update(status="frozen")

# Query 17: Bulk update deducting 5 percent fee from all active accounts.
# F() ensures each account gets its own 5 percent calculated correctly.
Account.objects.filter(status="active").update(
    balance=F("balance") - F("balance") * Decimal("0.05")
)


if __name__ == "__main__":
    print(list(active_accounts.values("account_number", "user__username")))
    print(list(users_with_account_count.values("username", "account_count")))
    print(list(balance_by_type))
    print(list(recent_or_large_txns.values("id", "amount", "status")))
    print(list(txns_with_tier.values("id", "amount", "tier")[:10]))
    print(
        list(accounts_with_latest_txn.values("account_number", "last_txn_amount")[:10])
    )
    print(list(high_confidence_users.values("username")))
    print(list(txns_with_running_total.values("id", "amount", "running_total")[:10]))
    print(
        list(
            merchant_stats.values(
                "name", "total_txns", "completed_txns", "total_revenue"
            )
        )
    )
    print(list(monthly_volume))
    print(list(healthy_accounts.values("account_number", "account_type")))
    print(list(card_display.values("display_name")[:10]))
