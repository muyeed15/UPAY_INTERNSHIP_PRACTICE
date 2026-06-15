from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import AccountViewSet
from transactions.views import TransactionViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet)
router.register("transactions", TransactionViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/", include(router.urls)),
]
