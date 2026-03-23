from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue, Notification

User = get_user_model()


class BulkOperationsTestCase(APITestCase):
    """Тесты массовых операций (bulk approve/reject)."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='emp1', password='pass12345')
        self.user2 = User.objects.create_user(username='emp2', password='pass12345')
        self.admin = User.objects.create_user(
            username='manager', password='pass12345', is_staff=True
        )

        group = KpiGroup.objects.create(name='Bulk Test', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group, name='Bulk Indicator',
            max_value=10.0, weight=1.0, data_source='manual', order=1
        )

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def _create_submitted_value(self, user, period):
        return KpiValue.objects.create(
            user=user, indicator=self.indicator,
            period=period, actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_SUBMITTED
        )

    def test_bulk_approve(self):
        """Массовое одобрение нескольких KPI."""
        v1 = self._create_submitted_value(self.user1, '2025-01')
        v2 = self._create_submitted_value(self.user2, '2025-01')

        response = self.admin_client.post(
            reverse('kpivalue-bulk-approve'),
            {'ids': [v1.id, v2.id], 'review_comment': 'Bulk OK'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['approved'], 2)

        v1.refresh_from_db()
        v2.refresh_from_db()
        self.assertEqual(v1.status, KpiValue.STATUS_APPROVED)
        self.assertEqual(v2.status, KpiValue.STATUS_APPROVED)
        self.assertTrue(v1.is_verified)

    def test_bulk_reject(self):
        """Массовое отклонение нескольких KPI."""
        v1 = self._create_submitted_value(self.user1, '2025-02')
        v2 = self._create_submitted_value(self.user2, '2025-02')

        response = self.admin_client.post(
            reverse('kpivalue-bulk-reject'),
            {'ids': [v1.id, v2.id], 'review_comment': 'Needs work'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rejected'], 2)

        v1.refresh_from_db()
        v2.refresh_from_db()
        self.assertEqual(v1.status, KpiValue.STATUS_REJECTED)
        self.assertEqual(v2.status, KpiValue.STATUS_REJECTED)

    def test_bulk_approve_creates_notifications(self):
        """Массовое одобрение создаёт уведомления для каждого пользователя."""
        v1 = self._create_submitted_value(self.user1, '2025-03')
        v2 = self._create_submitted_value(self.user2, '2025-03')

        self.admin_client.post(
            reverse('kpivalue-bulk-approve'),
            {'ids': [v1.id, v2.id]},
            format='json'
        )

        notif_user1 = Notification.objects.filter(
            recipient=self.user1, notification_type=Notification.TYPE_APPROVED
        ).count()
        notif_user2 = Notification.objects.filter(
            recipient=self.user2, notification_type=Notification.TYPE_APPROVED
        ).count()
        self.assertEqual(notif_user1, 1)
        self.assertEqual(notif_user2, 1)

    def test_bulk_approve_skips_non_submitted(self):
        """Массовое одобрение пропускает не-submitted значения."""
        v1 = self._create_submitted_value(self.user1, '2025-04')
        v2 = KpiValue.objects.create(
            user=self.user2, indicator=self.indicator,
            period='2025-04', actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_DRAFT
        )

        response = self.admin_client.post(
            reverse('kpivalue-bulk-approve'),
            {'ids': [v1.id, v2.id]},
            format='json'
        )
        self.assertEqual(response.data['approved'], 1)

        v2.refresh_from_db()
        self.assertEqual(v2.status, KpiValue.STATUS_DRAFT)

    def test_bulk_approve_empty_ids(self):
        """Массовое одобрение с пустым списком — ошибка валидации."""
        response = self.admin_client.post(
            reverse('kpivalue-bulk-approve'),
            {'ids': []},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_reject_empty_ids(self):
        """Массовое отклонение с пустым списком — ошибка валидации."""
        response = self.admin_client.post(
            reverse('kpivalue-bulk-reject'),
            {'ids': []},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
