import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

ORCID_PATTERN = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$')


class UserProfileView(APIView):
    """
    Профиль текущего пользователя.

    GET  /api/kpi/profile/ — получить данные профиля
    PATCH /api/kpi/profile/ — обновить профиль
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, 'profile', None)

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'orcid': profile.orcid if profile else None,
            'department': profile.department if profile else '',
            'position': profile.position if profile else '',
            'role': profile.role if profile else 'pps',
            'role_display': profile.get_role_display() if profile else 'ППС (преподаватель)',
        })

    def patch(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        # Обновление полей User
        allowed_user_fields = ('first_name', 'last_name', 'email')
        user_changed = False
        for field in allowed_user_fields:
            if field in data:
                setattr(user, field, data[field])
                user_changed = True
        if user_changed:
            user.save(update_fields=[f for f in allowed_user_fields if f in data])

        # Обновление полей профиля
        profile = getattr(user, 'profile', None)
        if profile is None:
            from apps.kpi.models import UserProfile
            profile = UserProfile.objects.create(user=user)

        profile_changed = False

        if 'orcid' in data:
            orcid = (data['orcid'] or '').strip().upper()
            if orcid and not ORCID_PATTERN.match(orcid):
                return Response(
                    {'error': 'Неверный формат ORCID. Ожидается: 0000-0000-0000-0000'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.orcid = orcid or None
            profile_changed = True

        if 'role' in data:
            role_value = (data['role'] or '').strip().lower()
            if role_value in ('pps', 'rop'):
                profile.role = role_value
                profile_changed = True

        if 'department' in data:
            profile.department = (data['department'] or '').strip()
            profile_changed = True

        if 'position' in data:
            profile.position = (data['position'] or '').strip()
            profile_changed = True

        if profile_changed:
            profile.save()

        return self.get(request)
