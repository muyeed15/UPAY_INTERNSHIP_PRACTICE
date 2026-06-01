from random import choice, randint, uniform
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fintech.models import UserProfile, Account, Transaction, Card, Merchant


class Command(BaseCommand):
    help = "Seed fintech database with sample data"

    def handle(self, *args, **kwargs):
        if User.objects.filter(username="alice").exists():
            self.stdout.write(self.style.WARNING("Data already seeded"))
            return

        merchants = []
        merchant_data = [
            ("Daraz", "DRZ", "retail", "BD"),
            ("Foodpanda", "FPDA", "food", "BD"),
            ("Pathao", "PTO", "travel", "BD"),
            ("bKash", "BKS", "tech", "BD"),
            ("Square", "SQR", "healthcare", "BD"),
            ("Chorki", "CHK", "entertainment", "BD"),
            ("Titas Gas", "TITAS", "utilities", "BD"),
            ("Shwapno", "SWP", "retail", "BD"),
            ("Biman Air", "BIMAN", "travel", "BD"),
            ("Grameenphone", "GP", "tech", "BD"),
        ]
        for name, code, cat, country in merchant_data:
            m = Merchant.objects.create(
                name=name, merchant_code=code, category=cat, country=country
            )
            merchants.append(m)

        users_data = [
            ("alice", "alice@example.com", "+8801700000001"),
            ("bob", "bob@example.com", "+8801700000002"),
            ("carol", "carol@example.com", "+8801700000003"),
            ("dave", "dave@example.com", "+8801700000004"),
            ("eve", "eve@example.com", "+8801700000005"),
        ]

        accounts = []
        cards = []

        for username, email, phone in users_data:
            user = User.objects.create_user(
                username=username, email=email, password="password123"
            )
            UserProfile.objects.create(user=user, phone=phone, kyc_status="verified")

            checking = Account.objects.create(
                user=user,
                account_type="checking",
                account_number=f"CHK{randint(10000000, 99999999)}",
                currency="BDT",
                balance=Decimal(str(round(uniform(100000, 10000000), 2))),
            )
            savings = Account.objects.create(
                user=user,
                account_type="savings",
                account_number=f"SAV{randint(10000000, 99999999)}",
                currency="BDT",
                balance=Decimal(str(round(uniform(500000, 50000000), 2))),
            )
            accounts.extend([checking, savings])

            for acc in [checking, savings]:
                card = Card.objects.create(
                    user=user,
                    account=acc,
                    card_number=f"{randint(1000,9999)}{randint(1000,9999)}{randint(1000,9999)}{randint(1000,9999)}",
                    card_type="debit" if acc.account_type == "checking" else "debit",
                    card_network=choice(["visa", "mastercard"]),
                    expiry_month=randint(1, 12),
                    expiry_year=randint(2027, 2030),
                    cvv=str(randint(100, 999)),
                )
                cards.append(card)

        txn_types = ["deposit", "withdrawal", "payment", "transfer", "refund", "fee"]
        directions = {
            "deposit": "incoming",
            "withdrawal": "outgoing",
            "payment": "outgoing",
            "transfer": "outgoing",
            "refund": "incoming",
            "fee": "outgoing",
        }
        statuses = [
            "completed",
            "completed",
            "completed",
            "completed",
            "pending",
            "failed",
        ]

        for acc in accounts:
            for _ in range(randint(8, 15)):
                txn_type = choice(txn_types)
                Transaction.objects.create(
                    account=acc,
                    direction=directions[txn_type],
                    transaction_type=txn_type,
                    amount=Decimal(str(round(uniform(500, 50000), 2))),
                    description=f"{txn_type.capitalize()} transaction",
                    status=choice(statuses),
                    merchant=(
                        choice(merchants) if txn_type in ("payment", "refund") else None
                    ),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded: {len(users_data)} users, {len(accounts)} accounts, "
                f"{len(merchants)} merchants, {len(cards)} cards, "
                f"{Transaction.objects.count()} transactions"
            )
        )
