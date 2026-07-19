"""
Custom permission classes for the RBAC project.

Deliverable 1: 3+ reusable permission classes
Deliverable 2: RBAC system with 3 roles
Deliverable 3: Row-level security via object-level permissions

Supports:
- Built-in DRF permissions: IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
- Custom: IsAccountOwner, IsVerifiedUser, IsActiveAccount, HasRole
- Composable AND/OR logic via BasePermissionCombiner
- Object-level permission checks with guardian integration
"""

from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied


# ════════════════════════════════════════════════════════════════════════
# DELIVERABLE 1 — Custom Permission Classes
# ════════════════════════════════════════════════════════════════════════

class IsAccountOwner(BasePermission):
    """
    Object-level: grants access only if obj.user == request.user.
    Intended for detail/update/delete on owned resources.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsVerifiedUser(BasePermission):
    """
    Grants access only to users with is_verified == True.
    """
    message = 'Your account must be verified to perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_verified', False)
        )


class IsActiveAccount(BasePermission):
    """
    Grants access only to active (non-banned) users.
    """
    message = 'Your account is inactive.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )


class HasRole(BasePermission):
    """
    Grants access based on the user's role.

    Usage:
        permission_classes = [HasRole('admin', 'agent')]
        permission_classes = [HasRole('admin')]
    """
    def __init__(self, *allowed_roles):
        self.allowed_roles = set(allowed_roles)

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_role = getattr(request.user, 'role', None)
        return user_role in self.allowed_roles

    def __call__(self):
        return self


# ════════════════════════════════════════════════════════════════════════
# DELIVERABLE 1 (continued) — Composable AND / OR Permission Base
# ════════════════════════════════════════════════════════════════════════

class BasePermissionCombiner(BasePermission):
    """
    Base class that combines multiple permission classes with a logical operator.

    Subclasses must define `operator` as either 'AND' or 'OR'.
    """

    operator = None  # 'AND' or 'OR'

    def __init__(self, *permissions):
        self.permissions = permissions

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not self.permissions:
            return True
        results = [p().has_permission(request, view) for p in self.permissions]
        if self.operator == 'AND':
            return all(results)
        elif self.operator == 'OR':
            return any(results)
        raise NotImplementedError(f'Unknown operator: {self.operator}')

    def has_object_permission(self, request, view, obj):
        if not self.permissions:
            return True
        results = [p().has_object_permission(request, view, obj) for p in self.permissions]
        if self.operator == 'AND':
            return all(results)
        elif self.operator == 'OR':
            return any(results)
        raise NotImplementedError(f'Unknown operator: {self.operator}')


class AND(BasePermissionCombiner):
    """All listed permissions must pass."""
    operator = 'AND'


class OR(BasePermissionCombiner):
    """At least one listed permission must pass."""
    operator = 'OR'


# ════════════════════════════════════════════════════════════════════════
# DELIVERABLE 2 — RBAC Role-Specific Permission Classes
# ════════════════════════════════════════════════════════════════════════

class IsAdmin(HasRole):
    def __init__(self):
        super().__init__('admin')


class IsAgent(HasRole):
    def __init__(self):
        super().__init__('agent')


class IsCustomer(HasRole):
    def __init__(self):
        super().__init__('customer')


class IsAdminOrAgent(HasRole):
    def __init__(self):
        super().__init__('admin', 'agent')


# ════════════════════════════════════════════════════════════════════════
# DELIVERABLE 3 — Row-Level / Object-Level Security Mixins
# ════════════════════════════════════════════════════════════════════════

class IsTransactionOwner(IsAccountOwner):
    """
    Object-level permission that checks if the requesting user owns
    the Transaction (via obj.user == request.user).

    Admin users bypass this check and can access any transaction.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return super().has_object_permission(request, view, obj)


class IsOwnerOrAdminOrAgentReadOnly(BasePermission):
    """
    Owners have full access (CRUD).
    Admins have full access to everything.
    Agents can read (GET) any transaction but cannot modify.
    Customers can only access their own transactions.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Admins always pass
        if user.role == 'admin':
            return True

        # Agents can read anything
        if user.role == 'agent' and request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Owners can access their own data
        return obj.user == user
