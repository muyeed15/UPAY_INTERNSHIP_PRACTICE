from django.contrib import admin
from .models import UserProfile, Account, Transaction, Card, Merchant


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "kyc_status", "created_at"]
    list_filter = ["kyc_status"]
    search_fields = ["user__username", "phone"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        "account_number",
        "user",
        "account_type",
        "currency",
        "balance",
        "status",
    ]
    list_filter = ["account_type", "status", "currency"]
    search_fields = ["account_number", "user__username"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "account",
        "direction",
        "transaction_type",
        "amount",
        "status",
        "created_at",
    ]
    list_filter = ["transaction_type", "status", "direction", "created_at"]
    search_fields = ["account__account_number", "description"]


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = [
        "card_number",
        "user",
        "account",
        "card_type",
        "card_network",
        "status",
    ]
    list_filter = ["card_type", "card_network", "status"]
    search_fields = ["card_number", "user__username"]


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ["name", "merchant_code", "category", "country", "status"]
    list_filter = ["category", "status"]
    search_fields = ["name", "merchant_code"]
