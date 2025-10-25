from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware logic to restrict access to admin users only.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = request.user
        if not user.is_authenticated or not user.is_superuser:
            return JsonResponse({
                "meta": {"status": 403},
                "error": True,
                "message": "Access denied. Admins only."
            }, status=403)
        return None