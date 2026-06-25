import jwt
import os
from datetime import datetime, timedelta, timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import User


class JWTAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        # Extract Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        # Split the header into parts
        parts = auth_header.split()

        if len(parts) != 2:
            return None

        if parts[0].lower() != self.keyword.lower():
            return None

        token = parts[1]

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        try:
            payload = jwt.decode(
                key,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            # Return None to allow AllowAny views to work
            return None
        except jwt.InvalidTokenError:
            # Return None to allow AllowAny views to work
            return None

        try:
            user = User.objects.get(id=payload['id'])
        except User.DoesNotExist:
            # Return None to allow AllowAny views to work
            return None

        if not user.is_active:
            # Return None to allow AllowAny views to work
            return None

        return (user, key)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


def generate_token(user):
    """Generate JWT token for user"""
    role_name = ''
    try:
        role_name = user.role.name if user.role else ''
    except Exception:
        pass
    payload = {
        'id': str(user.id),
        'email': user.email,
        'role': role_name,
        'exp': datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token
