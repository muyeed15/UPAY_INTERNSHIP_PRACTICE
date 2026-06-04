from django.db import models
from accounts.models import Account


# Create your models here.
class Transaction(models.Model):
    TYPE_CHOICES = [("debit", "Debit"), ("credit", "Credit")]
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    is_reversed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} ${self.amount}"
