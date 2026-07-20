from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with test users and transactions'

    def handle(self, *args, **options):
        # ── Users ──────────────────────────────────────────────────────
        users_data = [
            {'username': 'admin_user', 'email': 'admin@test.com', 'password': 'pass1234', 'role': 'admin', 'is_verified': True},
            {'username': 'agent_jane', 'email': 'agent@test.com', 'password': 'pass1234', 'role': 'agent', 'is_verified': True},
            {'username': 'customer_bob', 'email': 'bob@test.com', 'password': 'pass1234', 'role': 'customer', 'is_verified': True},
            {'username': 'customer_alice', 'email': 'alice@test.com', 'password': 'pass1234', 'role': 'customer', 'is_verified': True},
            {'username': 'unverified_eve', 'email': 'eve@test.com', 'password': 'pass1234', 'role': 'customer', 'is_verified': False},
            {'username': 'banned_user', 'email': 'banned@test.com', 'password': 'pass1234', 'role': 'customer', 'is_verified': True, 'is_active': False},
        ]

        created_users = {}
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'role': data['role'],
                    'is_verified': data['is_verified'],
                    'is_active': data.get('is_active', True),
                },
            )
            if created:
                user.set_password(data['password'])
                user.save()
            created_users[data['username']] = user
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] {user}')

        # ── Transactions ───────────────────────────────────────────────
        from transactions.models import Transaction
        txns_data = [
            ('customer_bob', 150.00, 'Grocery payment'),
            ('customer_bob', 89.99, 'Electric bill'),
            ('customer_alice', 250.00, 'Rent transfer'),
            ('customer_alice', 45.00, 'Coffee subscription'),
            ('customer_bob', 500.00, 'Freelance income'),
        ]

        for username, amount, desc in txns_data:
            txn, created = Transaction.objects.get_or_create(
                user=created_users[username],
                amount=amount,
                description=desc,
                defaults={'status': 'completed'},
            )
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  [{status}] Transaction #{txn.pk} — {username} — {amount}')

        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))
