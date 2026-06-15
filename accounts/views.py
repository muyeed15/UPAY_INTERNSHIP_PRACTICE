from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account
from .serializers import (
    AccountSerializer,
    AccountDetailSerializer,
    AccountStatementSerializer,
)
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Account.objects.none()
        return Account.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AccountDetailSerializer
        if self.action == "statement":
            return AccountStatementSerializer
        return AccountSerializer

    @action(detail=True, methods=["post"])
    def freeze(self, request, pk=None):
        account = self.get_object()
        account.is_frozen = not account.is_frozen
        account.save()
        return Response({"status": "frozen" if account.is_frozen else "unfrozen"})

    @action(detail=True, methods=["get"])
    def statement(self, request, pk=None):
        account = self.get_object()
        serializer = AccountStatementSerializer(account)
        return Response(serializer.data)
