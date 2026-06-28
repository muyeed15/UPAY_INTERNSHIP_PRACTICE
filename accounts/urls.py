from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('sessions/<int:session_id>/revoke/', views.SessionRevokeView.as_view(), name='session_revoke'),
    path('sessions/revoke-all/', views.SessionRevokeAllView.as_view(), name='session_revoke_all'),
]
