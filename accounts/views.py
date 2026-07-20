from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, UserSerializer
from .permissions import IsVerifiedUser, IsActiveAccount, AND

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    permission_classes = [AND(permissions.IsAuthenticated, IsActiveAccount)]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    """
    Admin-only: list all users.
    Demonstrates built-in IsAdminUser + custom role check.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
