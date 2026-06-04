# from django.urls import path
# from .views import (
#     AccountListView,
#     AccountCreateView,
#     AccountUpdateView,
#     AccountDeleteView,
# )
# from .views_api import AccountAPIView
# from .views_api import AccountAPIView, AccountGenericView

# urlpatterns = [
#     path("", AccountListView.as_view(), name="account-list"),
#     path("create/", AccountCreateView.as_view(), name="account-create"),
#     path("<int:pk>/edit/", AccountUpdateView.as_view(), name="account-update"),
#     path("<int:pk>/delete/", AccountDeleteView.as_view(), name="account-delete"),
#     path("api/raw/", AccountAPIView.as_view(), name="account-api-raw"),
#     path("api/generic/", AccountGenericView.as_view(), name="account-api-generic"),
# ]

from django.urls import path
from .views_api import AccountAPIView, AccountGenericView

urlpatterns = [
    path("api/raw/", AccountAPIView.as_view(), name="account-api-raw"),
    path("api/generic/", AccountGenericView.as_view(), name="account-api-generic"),
]
