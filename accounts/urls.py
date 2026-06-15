from django.urls import path
from .views_api import AccountAPIView, AccountGenericView

urlpatterns = [
    path("api/raw/", AccountAPIView.as_view(), name="account-api-raw"),
    path("api/generic/", AccountGenericView.as_view(), name="account-api-generic"),
]
