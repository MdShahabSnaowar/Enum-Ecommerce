import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from .models import User


def is_admin_from_token(token):
    """
    Checks if the user from the provided JWT token is an admin.
    Returns (is_admin: bool, user: User or None)
    """
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if not user_id:
            raise AuthenticationFailed("Invalid token — user ID missing")

        # Fetch user
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationFailed("User not found")

        # Check role
        is_admin = user.is_superuser or (user.role and user.role.name.lower() == "admin")
        return is_admin, user

    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired")
    except jwt.DecodeError:
        raise AuthenticationFailed("Invalid token")
