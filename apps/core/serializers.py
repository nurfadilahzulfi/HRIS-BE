from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT claims with user info to avoid extra API calls on login."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role']  = user.role
        token['entity_id'] = user.entity_id
        if user.employee:
            token['employee_id'] = user.employee.id
            token['full_name']   = user.employee.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        data['user'] = {
            'id':        user.id,
            'email':     user.email,
            'role':      user.role,
            'full_name': user.full_name,
            'entity_id': user.entity_id,
        }
        return data


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer for /auth/me/ endpoint."""
    full_name   = serializers.CharField(read_only=True)
    employee_id = serializers.IntegerField(source='employee.id', read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'role', 'full_name',
            'entity_id', 'employee_id', 'is_active', 'date_joined',
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Password lama tidak sesuai.')
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
