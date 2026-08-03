from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, LogoutView, LogoutAllView, MeView, ChangePasswordView

urlpatterns = [
    path('auth/login/',           LoginView.as_view(),          name='auth-login'),
    path('auth/token/refresh/',   TokenRefreshView.as_view(),   name='auth-token-refresh'),
    path('auth/logout/',          LogoutView.as_view(),         name='auth-logout'),
    path('auth/logout-all/',      LogoutAllView.as_view(),      name='auth-logout-all'),
    path('auth/me/',              MeView.as_view(),             name='auth-me'),
    path('auth/me/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
]
