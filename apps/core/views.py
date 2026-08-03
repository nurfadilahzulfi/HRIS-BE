from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserMeSerializer,
    ChangePasswordSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Login with email + password → returns access & refresh JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(tags=['auth'], summary='Login')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklist the refresh token to invalidate session.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['auth'], summary='Logout')
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'success': False, 'message': 'Refresh token wajib diisi.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'success': True, 'message': 'Logout berhasil.'})
        except Exception:
            return Response(
                {'success': False, 'message': 'Token tidak valid.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutAllView(APIView):
    """
    POST /api/v1/auth/logout-all/
    Blacklist all active refresh tokens for the current user (logout from all devices).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['auth'], summary='Logout from all devices')
    def post(self, request):
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            tokens = OutstandingToken.objects.filter(user=request.user)
            count = 0
            for token in tokens:
                _, created = BlacklistedToken.objects.get_or_create(token=token)
                if created:
                    count += 1
            return Response({
                'success': True,
                'message': f'Logout dari seluruh perangkat berhasil. {count} token telah di-blacklist.'
            })
        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """
    GET  /api/v1/auth/me/  → current user profile
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['auth'], summary='Get current user profile')
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response({'success': True, 'data': serializer.data})


class ChangePasswordView(APIView):
    """
    PATCH /api/v1/auth/me/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=['auth'], summary='Change password')
    def patch(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'message': 'Password berhasil diubah.'})
