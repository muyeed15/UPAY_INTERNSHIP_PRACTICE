# from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# from django.urls import reverse_lazy
# from .models import Account


# # Create your views here.
# class AccountListView(ListView):
#     model = Account
#     template_name = "accounts/account_list.html"
#     context_object_name = "accounts"


# class AccountCreateView(CreateView):
#     model = Account
#     fields = ["user", "account_number", "balance"]
#     success_url = reverse_lazy("account-list")


# class AccountUpdateView(UpdateView):
#     model = Account
#     fields = ["user", "account_number", "balance"]
#     success_url = reverse_lazy("account-list")


# class AccountDeleteView(DeleteView):
#     model = Account
#     success_url = reverse_lazy("account-list")


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Account
from .serializers import AccountSerializer, AccountDetailSerializer
from transactions.models import Transaction


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
        transactions = Transaction.objects.filter(account=account)
        from transactions.serializers import TransactionSerializer

        serializer = TransactionSerializer(transactions, many=True)
        return Response(
            {
                "account": AccountSerializer(account).data,
                "transactions": serializer.data,
            }
        )
