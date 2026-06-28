from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from rest_framework import serializers, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTRefreshView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import UserSession
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    SessionSerializer,
)

User = get_user_model()


def _get_ip(request):
    # get client IP, handling proxies via X-Forwarded-For
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _get_device(request):
    ua = request.META.get('HTTP_USER_AGENT', '').lower()
    if not ua:
        return 'Unknown'
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        return 'Mobile'
    if 'tablet' in ua or 'ipad' in ua:
        return 'Tablet'
    return 'Desktop'


def _create_session(user, refresh_token, request):
    # save a session record with device, ip and expiry info
    token = refresh_token if isinstance(refresh_token, RefreshToken) else RefreshToken(refresh_token)
    UserSession.objects.create(
        user=user,
        refresh_token_jti=token['jti'],
        device=_get_device(request),
        ip_address=_get_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        expires_at=datetime.fromtimestamp(token['exp'], tz=timezone.utc),
    )


def _blacklist_jti(jti):
    # blacklist a token so it can't be used again
    try:
        ot = OutstandingToken.objects.get(jti=jti)
        BlacklistedToken.objects.get_or_create(token=ot)
        return True
    except OutstandingToken.DoesNotExist:
        return False


class RegisterView(APIView):
    # creates a new user and returns JWT tokens
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['account_id'] = user.account_id or ''

        _create_session(user, refresh, request)

        return Response({
            'message': 'Registration successful.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    # handles email+password login, returns JWT pair
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = RefreshToken(serializer.validated_data['refresh'])
        user = User.objects.get(id=refresh['user_id'])
        _create_session(user, refresh, request)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    # blacklists the refresh token and ends the session
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_str = request.data.get('refresh')
        if not refresh_str:
            return Response({'error': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_str)
            token.blacklist()
        except Exception:
            return Response({'error': 'Invalid or expired refresh token.'}, status=status.HTTP_400_BAD_REQUEST)

        UserSession.objects.filter(refresh_token_jti=token['jti']).update(is_active=False)
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class TokenRefreshView(SimpleJWTRefreshView):
    # rotates tokens -- blacklists old, issues new, tracks session

    def post(self, request, *args, **kwargs):
        old_refresh_str = request.data.get('refresh', '')
        try:
            old_jti = RefreshToken(old_refresh_str)['jti']
        except Exception:
            old_jti = None

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and old_jti:
            UserSession.objects.filter(refresh_token_jti=old_jti).update(is_active=False)
            new_refresh = response.data.get('refresh')
            if new_refresh:
                token = RefreshToken(new_refresh)
                user = User.objects.get(id=token['user_id'])
                _create_session(user, token, request)

        return response


class SessionListView(APIView):
    # shows all active and inactive sessions for the logged-in user
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SessionRevokeView(APIView):
    # kills a single session by id
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True,
            )
        except UserSession.DoesNotExist:
            return Response(
                {'error': 'Active session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        _blacklist_jti(session.refresh_token_jti)
        session.is_active = False
        session.save(update_fields=['is_active'])

        return Response({'message': 'Session revoked.'}, status=status.HTTP_200_OK)


class SessionRevokeAllView(APIView):
    # kills every active session for the user at once
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sessions = UserSession.objects.filter(user=request.user, is_active=True)
        for session in sessions:
            _blacklist_jti(session.refresh_token_jti)
            session.is_active = False
            session.save(update_fields=['is_active'])

        return Response({'message': 'All sessions revoked.'}, status=status.HTTP_200_OK)


class EmailAuthTokenSerializer(AuthTokenSerializer):
    # converts DRF TokenAuth to use email instead of username
    username = None
    email = serializers.EmailField(label='Email', write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        user = authenticate(
            request=self.context.get('request'),
            email=attrs.get('email'),
            password=attrs.get('password'),
        )
        if not user:
            raise serializers.ValidationError('Invalid email or password.', code='authorization')
        attrs['user'] = user
        return attrs


class EmailObtainAuthToken(ObtainAuthToken):
    serializer_class = EmailAuthTokenSerializer
