from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """
    Доступ только владельцу объекта или администратору.
    Объект должен иметь поле `user`.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user_id == request.user.id
