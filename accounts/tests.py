import json
import base64

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import User, UserSession

User = get_user_model()


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register/'

    def test_register_success(self):
        resp = self.client.post(self.url, {
            'email': 'new@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(email='dup@example.com', password='testpass123')
        resp = self.client.post(self.url, {
            'email': 'dup@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        resp = self.client.post(self.url, {
            'email': 'short@example.com',
            'password': '123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_creates_session(self):
        resp = self.client.post(self.url, {
            'email': 'session@example.com',
            'password': 'testpass123',
        }, format='json')
        user = User.objects.get(email='session@example.com')
        self.assertEqual(UserSession.objects.filter(user=user).count(), 1)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/login/'
        self.user = User.objects.create_user(
            email='login@example.com',
            password='testpass123',
            role='admin',
            account_id='ACC-LOGIN-001',
        )

    def test_login_success(self):
        resp = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_invalid_email(self):
        resp = self.client.post(self.url, {
            'email': 'wrong@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_invalid_password(self):
        resp = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'wrongpass',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        resp = self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_creates_session(self):
        self.client.post(self.url, {
            'email': 'login@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 1)


class LogoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='logout@example.com',
            password='testpass123',
        )
        resp = self.client.post('/api/login/', {
            'email': 'logout@example.com',
            'password': 'testpass123',
        }, format='json')
        self.access = resp.data['access']
        self.refresh = resp.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_logout_success(self):
        resp = self.client.post('/api/logout/', {
            'refresh': self.refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        session = UserSession.objects.filter(user=self.user).first()
        self.assertFalse(session.is_active)

    def test_logout_invalid_token(self):
        resp = self.client.post('/api/logout/', {
            'refresh': 'invalidtoken',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_without_token(self):
        resp = self.client.post('/api/logout/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_requires_auth(self):
        unauth_client = APIClient()
        resp = unauth_client.post('/api/logout/', {
            'refresh': self.refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTCustomClaimsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='claims@example.com',
            password='testpass123',
            role='moderator',
            account_id='ACC-CLAIMS-001',
        )

    @staticmethod
    def _decode_jwt(token):
        parts = token.split('.')
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))

    def test_login_token_has_custom_claims(self):
        resp = self.client.post('/api/login/', {
            'email': 'claims@example.com',
            'password': 'testpass123',
        }, format='json')
        payload = self._decode_jwt(resp.data['access'])
        self.assertEqual(payload['role'], 'moderator')
        self.assertEqual(payload['account_id'], 'ACC-CLAIMS-001')

    def test_register_token_has_custom_claims(self):
        resp = self.client.post('/api/register/', {
            'email': 'regclaims@example.com',
            'password': 'testpass123',
        }, format='json')
        payload = self._decode_jwt(resp.data['access'])
        self.assertEqual(payload['role'], 'user')
        self.assertEqual(payload['account_id'], '')

    def test_refresh_token_has_custom_claims(self):
        resp = self.client.post('/api/login/', {
            'email': 'claims@example.com',
            'password': 'testpass123',
        }, format='json')
        refresh = resp.data['refresh']
        resp = self.client.post('/api/token/refresh/', {
            'refresh': refresh,
        }, format='json')
        payload = self._decode_jwt(resp.data['access'])
        self.assertEqual(payload['role'], 'moderator')
        self.assertEqual(payload['account_id'], 'ACC-CLAIMS-001')


class RefreshTokenRotationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='rotate@example.com',
            password='testpass123',
        )
        resp = self.client.post('/api/login/', {
            'email': 'rotate@example.com',
            'password': 'testpass123',
        }, format='json')
        self.access = resp.data['access']
        self.refresh = resp.data['refresh']

    def test_refresh_returns_new_token_pair(self):
        resp = self.client.post('/api/token/refresh/', {
            'refresh': self.refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertNotEqual(resp.data['refresh'], self.refresh)

    def test_old_token_blacklisted_after_refresh(self):
        old_refresh = self.refresh
        resp = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh,
        }, format='json')
        new_refresh = resp.data['refresh']

        resp = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.post('/api/token/refresh/', {
            'refresh': new_refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_old_session_inactive_after_refresh(self):
        old_refresh = self.refresh
        resp = self.client.post('/api/token/refresh/', {
            'refresh': old_refresh,
        }, format='json')

        sessions = UserSession.objects.filter(user=self.user)
        self.assertEqual(sessions.count(), 2)
        old_jti = sessions.filter(refresh_token_jti__isnull=False).order_by('id')[0]
        self.assertFalse(old_jti.is_active)
        new_jti = sessions.order_by('-id')[0]
        self.assertTrue(new_jti.is_active)


class SessionManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='sessionmgmt@example.com',
            password='testpass123',
        )
        resp = self.client.post('/api/login/', {
            'email': 'sessionmgmt@example.com',
            'password': 'testpass123',
        }, format='json')
        self.access1 = resp.data['access']
        self.refresh1 = resp.data['refresh']

        resp = self.client.post('/api/login/', {
            'email': 'sessionmgmt@example.com',
            'password': 'testpass123',
        }, format='json')
        self.access2 = resp.data['access']
        self.refresh2 = resp.data['refresh']

    def test_list_sessions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access1}')
        resp = self.client.get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_list_sessions_requires_auth(self):
        unauth_client = APIClient()
        resp = unauth_client.get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoke_session(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access1}')
        sessions = UserSession.objects.filter(user=self.user, is_active=True)
        session_id = sessions.first().id

        resp = self.client.post(f'/api/sessions/{session_id}/revoke/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertEqual(sessions.count(), 1)

    def test_revoke_others_session_fails(self):
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
        )
        resp = self.client.post('/api/login/', {
            'email': 'other@example.com',
            'password': 'testpass123',
        }, format='json')

        other_session_id = UserSession.objects.filter(user=other_user).first().id

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access1}')
        resp = self.client.post(f'/api/sessions/{other_session_id}/revoke/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_revoke_all_sessions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access1}')
        resp = self.client.post('/api/sessions/revoke-all/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertEqual(sessions.count(), 0)

    def test_revoke_nonexistent_session(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access1}')
        resp = self.client.post('/api/sessions/99999/revoke/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_session_has_device_and_ip(self):
        session = UserSession.objects.filter(user=self.user).first()
        self.assertIsNotNone(session.device)
        self.assertIsNotNone(session.ip_address)
        self.assertIsNotNone(session.expires_at)


class EmailBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='backend@example.com',
            password='testpass123',
        )

    def test_authenticate_with_email(self):
        from django.contrib.auth import authenticate
        user = authenticate(
            email='backend@example.com',
            password='testpass123',
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'backend@example.com')

    def test_authenticate_wrong_password(self):
        from django.contrib.auth import authenticate
        user = authenticate(
            email='backend@example.com',
            password='wrongpass',
        )
        self.assertIsNone(user)

    def test_authenticate_nonexistent_email(self):
        from django.contrib.auth import authenticate
        user = authenticate(
            email='nobody@example.com',
            password='testpass123',
        )
        self.assertIsNone(user)

    def test_authenticate_missing_email(self):
        from django.contrib.auth import authenticate
        user = authenticate(password='testpass123')
        self.assertIsNone(user)


class DRFTokenAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='drftoken@example.com',
            password='testpass123',
        )

    def test_obtain_token_with_email(self):
        resp = self.client.post('/api/token-auth/', {
            'email': 'drftoken@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)

    def test_obtain_token_bad_credentials(self):
        resp = self.client.post('/api/token-auth/', {
            'email': 'drftoken@example.com',
            'password': 'wrong',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_auth_access_protected(self):
        resp = self.client.post('/api/token-auth/', {
            'email': 'drftoken@example.com',
            'password': 'testpass123',
        }, format='json')
        token = resp.data['token']

        unauth_client = APIClient()
        unauth_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = unauth_client.get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class SimpleJWTBuiltinTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='builtin@example.com',
            password='testpass123',
            role='admin',
            account_id='ACC-BUILTIN',
        )

    def test_obtain_jwt_pair(self):
        resp = self.client.post('/api/token/', {
            'email': 'builtin@example.com',
            'password': 'testpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_jwt_has_custom_claims(self):
        resp = self.client.post('/api/token/', {
            'email': 'builtin@example.com',
            'password': 'testpass123',
        }, format='json')
        parts = resp.data['access'].split('.')
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload))
        self.assertEqual(payload['role'], 'admin')
        self.assertEqual(payload['account_id'], 'ACC-BUILTIN')

    def test_jwt_verify(self):
        resp = self.client.post('/api/token/', {
            'email': 'builtin@example.com',
            'password': 'testpass123',
        }, format='json')
        token = resp.data['access']

        resp = self.client.post('/api/token/verify/', {
            'token': token,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_jwt_verify_invalid(self):
        resp = self.client.post('/api/token/verify/', {
            'token': 'invalid.token.here',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_access_protected(self):
        resp = self.client.post('/api/token/', {
            'email': 'builtin@example.com',
            'password': 'testpass123',
        }, format='json')
        access = resp.data['access']

        unauth_client = APIClient()
        unauth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = unauth_client.get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class SecurityTokenLeakageTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='security@example.com',
            password='testpass123',
        )

    def test_stolen_refresh_cannot_rotate(self):
        resp = self.client.post('/api/login/', {
            'email': 'security@example.com',
            'password': 'testpass123',
        }, format='json')
        stolen_refresh = resp.data['refresh']

        resp = self.client.post('/api/token/refresh/', {
            'refresh': stolen_refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post('/api/token/refresh/', {
            'refresh': stolen_refresh,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accesstoken_expiry_enforced(self):
        from datetime import timedelta
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=0))
        short_lived = str(token)

        unauth_client = APIClient()
        unauth_client.credentials(HTTP_AUTHORIZATION=f'Bearer {short_lived}')
        resp = unauth_client.get('/api/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
