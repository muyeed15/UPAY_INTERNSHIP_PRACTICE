from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    # Function-based alternative endpoints (must come before router to avoid pk collision)
    path('fbv/', views.transaction_list_create, name='txn-list-create-fbv'),
    path('fbv/<int:pk>/', views.transaction_detail, name='txn-detail-fbv'),
    # ViewSet-based CRUD
    path('', include(router.urls)),
    # Demo / test endpoints for permission combinations
    path('demo/authenticated/', views.demo_authenticated_only, name='demo-authenticated'),
    path('demo/admin/', views.demo_admin_only, name='demo-admin'),
    path('demo/auth-readonly/', views.demo_auth_or_readonly, name='demo-auth-readonly'),
    path('demo/admin-role/', views.demo_admin_role, name='demo-admin-role'),
    path('demo/agent-role/', views.demo_agent_role, name='demo-agent-role'),
    path('demo/customer-role/', views.demo_customer_role, name='demo-customer-role'),
    path('demo/admin-or-agent/', views.demo_admin_or_agent, name='demo-admin-or-agent'),
    path('demo/admin-or-verified/', views.demo_admin_or_verified, name='demo-admin-or-verified'),
    path('demo/verified-and-active/', views.demo_verified_and_active, name='demo-verified-and-active'),
]
