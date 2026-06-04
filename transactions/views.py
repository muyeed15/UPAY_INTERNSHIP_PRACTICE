from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Transaction.objects.none()
        return Transaction.objects.filter(account__user=self.request.user)

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        transaction = self.get_object()
        if transaction.is_reversed:
            return Response(
                {"error": "Already reversed"}, status=status.HTTP_400_BAD_REQUEST
            )
        transaction.is_reversed = True
        transaction.save()
        account = transaction.account
        if transaction.type == "debit":
            account.balance += transaction.amount
        else:
            account.balance -= transaction.amount
        account.save()
        return Response({"status": "reversed"})
