import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.kpi.models import get_user_kpi_role

User = get_user_model()

ORCID_PATTERN = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$')

AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2 MB
AVATAR_ALLOWED_TYPES = ('image/jpeg', 'image/png', 'image/webp')


class UserProfileView(APIView):
    """
    Профиль текущего пользователя.

    GET  /api/kpi/profile/ — получить данные профиля
    PATCH /api/kpi/profile/ — обновить профиль
    """
    permission_classes = [IsAuthenticated]

    def _get_profile(self, user):
        profile = getattr(user, 'profile', None)
        if profile is None:
            from apps.kpi.models import UserProfile
            profile = UserProfile.objects.create(user=user)
        return profile

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = self._get_profile(user)

        avatar_url = None
        if profile.avatar:
            avatar_url = request.build_absolute_uri(profile.avatar.url)

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
            'avatar': avatar_url,
            'role': get_user_kpi_role(user),
            'role_display': 'РОП (руководитель)' if get_user_kpi_role(user) == 'rop' else 'ППС (преподаватель)',
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
        profile = self._get_profile(user)
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

        # Роль нельзя менять через профиль — управляется администратором

        if 'department' in data:
            profile.department = (data['department'] or '').strip()
            profile_changed = True

        if 'position' in data:
            profile.position = (data['position'] or '').strip()
            profile_changed = True

        if profile_changed:
            profile.save()

        return self.get(request)


class ChangePasswordView(APIView):
    """
    POST /api/kpi/profile/change-password/
    Body: {current_password, new_password}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')

        if not current_password or not new_password:
            return Response(
                {'error': 'Укажите текущий и новый пароль'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_password) < 8:
            return Response(
                {'error': 'Новый пароль должен быть не менее 8 символов'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(current_password):
            return Response(
                {'error': 'Неверный текущий пароль'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])

        return Response({'message': 'Пароль успешно изменён'})


class AvatarUploadView(APIView):
    """
    POST /api/kpi/profile/avatar/ — загрузить аватар
    DELETE /api/kpi/profile/avatar/ — удалить аватар
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def _get_profile(self, user):
        profile = getattr(user, 'profile', None)
        if profile is None:
            from apps.kpi.models import UserProfile
            profile = UserProfile.objects.create(user=user)
        return profile

    def post(self, request):
        avatar = request.FILES.get('avatar')
        if not avatar:
            return Response(
                {'error': 'Файл не прикреплён'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if avatar.content_type not in AVATAR_ALLOWED_TYPES:
            return Response(
                {'error': 'Допустимые форматы: JPEG, PNG, WebP'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if avatar.size > AVATAR_MAX_SIZE:
            return Response(
                {'error': 'Максимальный размер файла — 2 МБ'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = self._get_profile(request.user)

        # Удаляем старый аватар
        if profile.avatar:
            profile.avatar.delete(save=False)

        profile.avatar = avatar
        profile.save(update_fields=['avatar'])

        avatar_url = request.build_absolute_uri(profile.avatar.url)
        return Response({'avatar': avatar_url})

    def delete(self, request):
        profile = self._get_profile(request.user)
        if profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save(update_fields=['avatar'])
        return Response({'avatar': None})
