from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue

User = get_user_model()


class PermissionsTestCase(APITestCase):
    """Тесты безопасности и прав доступа."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass12345')
        self.user2 = User.objects.create_user(username='user2', password='pass12345')
        self.admin = User.objects.create_user(
            username='admin', password='pass12345', is_staff=True
        )

        group = KpiGroup.objects.create(name='Test', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group, name='Indicator',
            max_value=10.0, weight=1.0, data_source='manual', order=1
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def _create_value(self, user, period='2025-01'):
        return KpiValue.objects.create(
            user=user, indicator=self.indicator,
            period=period, actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_DRAFT
        )

    def test_user_cannot_edit_other_users_value(self):
        """Пользователь не может редактировать чужое значение KPI."""
        value = self._create_value(self.user1)

        response = self.client2.patch(
            reverse('kpivalue-detail', args=[value.id]),
            {'actual_value': 9.0}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_other_users_value(self):
        """Пользователь не может удалить чужое значение KPI."""
        value = self._create_value(self.user1)

        response = self.client2.delete(
            reverse('kpivalue-detail', args=[value.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_submit_other_users_value(self):
        """Пользователь не может подать чужое значение на проверку."""
        value = self._create_value(self.user1)

        response = self.client2.post(
            reverse('kpivalue-submit', args=[value.id]), {}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_access_manager_dashboard(self):
        """Обычный пользователь не может получить дашборд руководителя."""
        response = self.client1.get(reverse('manager-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_access_top_performers(self):
        """Обычный пользователь не может получить топ сотрудников."""
        response = self.client1.get(reverse('top-performers'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_approve_values(self):
        """Обычный пользователь не может одобрять KPI."""
        value = self._create_value(self.user1, period='2025-02')
        value.status = KpiValue.STATUS_SUBMITTED
        value.save()

        response = self.client2.post(
            reverse('kpivalue-approve', args=[value.id]),
            {'review_comment': 'hack'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_bulk_approve(self):
        """Обычный пользователь не может массово одобрять."""
        response = self.client1.post(
            reverse('kpivalue-bulk-approve'),
            {'ids': [1, 2]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_bulk_reject(self):
        """Обычный пользователь не может массово отклонять."""
        response = self.client1.post(
            reverse('kpivalue-bulk-reject'),
            {'ids': [1, 2]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_view_any_user_values(self):
        """Администратор может просматривать значения любого пользователя."""
        self._create_value(self.user1, period='2025-03')

        response = self.admin_client.get(
            reverse('kpivalue-list'),
            {'scope': 'all', 'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cannot_generate_report_for_other_user(self):
        """Обычный пользователь не может генерировать отчёт за другого."""
        response = self.client1.get(
            reverse('generate-user-report', args=[self.user2.id]),
            {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        """Неавторизованный доступ запрещён ко всем эндпоинтам."""
        anon = APIClient()
        endpoints = [
            reverse('kpivalue-list'),
            reverse('kpivalue-dashboard'),
            reverse('kpi-groups'),
            reverse('manual-kpi-indicators'),
            reverse('user-profile'),
        ]
        for url in endpoints:
            response = anon.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f'Endpoint {url} should require authentication'
            )

    def test_cannot_edit_approved_value(self):
        """Нельзя редактировать одобренное значение."""
        value = self._create_value(self.user1, period='2025-04')
        value.status = KpiValue.STATUS_APPROVED
        value.is_verified = True
        value.save()

        response = self.client1.patch(
            reverse('kpivalue-detail', args=[value.id]),
            {'actual_value': 99.0}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_edit_submitted_value(self):
        """Нельзя редактировать значение на проверке."""
        value = self._create_value(self.user1, period='2025-05')
        value.status = KpiValue.STATUS_SUBMITTED
        value.save()

        response = self.client1.patch(
            reverse('kpivalue-detail', args=[value.id]),
            {'actual_value': 99.0}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_delete_approved_value(self):
        """Нельзя удалить одобренное значение."""
        value = self._create_value(self.user1, period='2025-06')
        value.status = KpiValue.STATUS_APPROVED
        value.is_verified = True
        value.save()

        response = self.client1.delete(
            reverse('kpivalue-detail', args=[value.id])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
