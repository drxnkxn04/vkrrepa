from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import UserProfile

User = get_user_model()


class UserProfileTestCase(APITestCase):
    """Тесты профиля пользователя."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass12345',
            first_name='Иван', last_name='Петров', email='ivan@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Получение профиля текущего пользователя."""
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Иван')
        self.assertEqual(response.data['last_name'], 'Петров')

    def test_update_user_fields(self):
        """Обновление полей User (имя, фамилия, email)."""
        response = self.client.patch(
            reverse('user-profile'),
            {'first_name': 'Алексей', 'email': 'alex@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Алексей')
        self.assertEqual(response.data['email'], 'alex@example.com')

    def test_update_orcid_valid(self):
        """Обновление ORCID с валидным форматом."""
        response = self.client.patch(
            reverse('user-profile'),
            {'orcid': '0000-0002-1825-0097'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['orcid'], '0000-0002-1825-0097')

    def test_update_orcid_invalid(self):
        """Обновление ORCID с невалидным форматом."""
        response = self.client.patch(
            reverse('user-profile'),
            {'orcid': 'invalid-orcid'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_role(self):
        """Обновление роли (pps/rop)."""
        response = self.client.patch(
            reverse('user-profile'),
            {'role': 'rop'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'rop')

    def test_update_department_and_position(self):
        """Обновление кафедры и должности."""
        response = self.client.patch(
            reverse('user-profile'),
            {'department': 'Центр ИИ', 'position': 'Доцент'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['department'], 'Центр ИИ')
        self.assertEqual(response.data['position'], 'Доцент')

    def test_profile_auto_created_on_patch(self):
        """Профиль создаётся автоматически при обновлении, если его нет."""
        # Удаляем профиль если он был создан сигналом
        UserProfile.objects.filter(user=self.user).delete()

        response = self.client.patch(
            reverse('user-profile'),
            {'department': 'Тест'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_clear_orcid(self):
        """Очистка ORCID (пустая строка)."""
        # Сначала установим
        self.client.patch(
            reverse('user-profile'),
            {'orcid': '0000-0002-1825-0097'},
            format='json'
        )
        # Затем очистим
        response = self.client.patch(
            reverse('user-profile'),
            {'orcid': ''},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['orcid'])

    def test_unauthenticated_cannot_access_profile(self):
        """Неавторизованный пользователь не имеет доступа к профилю."""
        anon = APIClient()
        response = anon.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
