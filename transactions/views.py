from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.exceptions import PermissionDenied

from .models import Transaction
from .serializers import TransactionSerializer
from accounts.permissions import (
    IsVerifiedUser,
    IsActiveAccount,
    IsAdmin,
    IsAgent,
    IsCustomer,
    IsAdminOrAgent,
    IsTransactionOwner,
    IsOwnerOrAdminOrAgentReadOnly,
    AND,
    OR,
    HasRole,
)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    CRUD for Transactions with role-based and object-level permissions.

    Permission matrix:
    - Admin: full CRUD on all transactions
    - Agent: list all, retrieve any, cannot create/update/delete
    - Customer: CRUD only own transactions

    Object-level (row-level) enforcement via get_object() override + permission classes.
    """
    serializer_class = TransactionSerializer

    # Base permission — authenticated + active + verified
    permission_classes = [AND(IsAuthenticated, IsActiveAccount, IsVerifiedUser)]

    def get_queryset(self):
        """
        List action: filter so customers only see their own transactions.
        Detail actions: return all — object-level check happens in get_object().
        """
        user = self.request.user
        if self.action == 'list':
            if user.role in ('admin', 'agent'):
                return Transaction.objects.all()
            return Transaction.objects.filter(user=user)
        if user.role in ('admin', 'agent'):
            return Transaction.objects.all()
        # For retrieve/update/destroy on customer, return all and let
        # check_object_permissions() in get_object() do the enforcement.
        # This ensures cross-account access gets 403 (not 404).
        return Transaction.objects.all()

    def get_permissions(self):
        """Fine-grained per-action permission resolution."""
        if self.action == 'create':
            return [p() for p in [IsAuthenticated, IsActiveAccount, IsVerifiedUser, IsCustomer]]
        if self.action == 'list':
            return [p() for p in [IsAuthenticated, IsActiveAccount, IsVerifiedUser]]
        if self.action == 'retrieve':
            return [IsOwnerOrAdminOrAgentReadOnly(), IsActiveAccount(), IsVerifiedUser()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsOwnerOrAdminOrAgentReadOnly(), IsActiveAccount(), IsVerifiedUser()]
        return super().get_permissions()

    def get_object(self):
        """Override to enforce object-level row-level security."""
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ─── Transaction List/Create View (function-based alternative) ───────────

@api_view(['GET', 'POST'])
@permission_classes([AND(IsAuthenticated, IsActiveAccount, IsVerifiedUser)])
def transaction_list_create(request):
    if request.method == 'GET':
        user = request.user
        if user.role == 'admin':
            qs = Transaction.objects.all()
        else:
            qs = Transaction.objects.filter(user=user)
        serializer = TransactionSerializer(qs, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.user.role != 'customer':
            raise PermissionDenied('Only customers can create transactions.')
        serializer = TransactionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── Transaction Detail View (function-based, object-level enforced) ─────

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsOwnerOrAdminOrAgentReadOnly, IsActiveAccount, IsVerifiedUser])
def transaction_detail(request, pk):
    try:
        txn = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Explicit object-level check
    user = request.user
    if user.role == 'admin':
        pass
    elif user.role == 'agent' and request.method in ('GET',):
        pass
    elif txn.user != user:
        raise PermissionDenied('You do not own this transaction.')

    if request.method == 'GET':
        serializer = TransactionSerializer(txn)
        return Response(serializer.data)

    if request.method in ('PUT', 'PATCH'):
        if user.role == 'agent':
            raise PermissionDenied('Agents cannot modify transactions.')
        serializer = TransactionSerializer(txn, data=request.data, partial=(request.method == 'PATCH'))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    if request.method == 'DELETE':
        if user.role == 'agent':
            raise PermissionDenied('Agents cannot delete transactions.')
        txn.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ════════════════════════════════════════════════════════════════════════
# Test / Demo Endpoints — Showcasing Permission Combinations
# ════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def demo_authenticated_only(request):
    """Accessible by any authenticated user."""
    return Response({'message': f'Hello {request.user.username}, you are authenticated!'})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def demo_admin_only(request):
    """Accessible only by staff/superusers (built-in IsAdminUser)."""
    return Response({'message': 'Admin-only endpoint reached.'})


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def demo_auth_or_readonly(request):
    """Readable by anyone, writable only by authenticated users."""
    if request.method == 'GET':
        return Response({'data': 'public read allowed'})
    return Response({'message': 'Write allowed for authenticated users only'})


@api_view(['GET'])
@permission_classes([IsAdmin])
def demo_admin_role(request):
    """Accessible only by users with role='admin'."""
    return Response({'message': 'Admin role endpoint.'})


@api_view(['GET'])
@permission_classes([IsAgent])
def demo_agent_role(request):
    """Accessible only by users with role='agent'."""
    return Response({'message': 'Agent role endpoint.'})


@api_view(['GET'])
@permission_classes([IsCustomer])
def demo_customer_role(request):
    """Accessible only by users with role='customer'."""
    return Response({'message': 'Customer role endpoint.'})


@api_view(['GET'])
@permission_classes([IsAdminOrAgent])
def demo_admin_or_agent(request):
    """Accessible by admin OR agent roles."""
    return Response({'message': 'Admin or Agent role endpoint.'})


@api_view(['GET'])
@permission_classes([OR(IsAdmin, IsVerifiedUser)])
def demo_admin_or_verified(request):
    """Accessible by admins OR verified users — showcases OR combinator."""
    return Response({'message': 'Admin or Verified user endpoint.'})


@api_view(['GET'])
@permission_classes([AND(IsVerifiedUser, IsActiveAccount)])
def demo_verified_and_active(request):
    """Accessible only by verified AND active users — showcases AND combinator."""
    return Response({'message': 'Verified AND Active user endpoint.'})
