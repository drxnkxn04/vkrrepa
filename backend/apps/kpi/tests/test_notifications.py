from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue, Notification

User = get_user_model()


class NotificationTestCase(APITestCase):
    """Тесты системы уведомлений."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='employee', password='pass12345'
        )
        self.admin = User.objects.create_user(
            username='manager', password='pass12345', is_staff=True
        )

        group = KpiGroup.objects.create(name='Test Group', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group, name='Test Indicator',
            max_value=10.0, weight=1.0, data_source='manual', order=1
        )

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def _create_notification(self, recipient, title='Test', message='Test msg'):
        return Notification.objects.create(
            recipient=recipient,
            notification_type=Notification.TYPE_SUBMITTED,
            title=title,
            message=message,
        )

    def test_user_sees_only_own_notifications(self):
        """Пользователь видит только свои уведомления."""
        self._create_notification(self.user, title='For user')
        self._create_notification(self.admin, title='For admin')

        response = self.user_client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'For user')

    def test_mark_notification_as_read(self):
        """Отметка уведомления как прочитанного."""
        notif = self._create_notification(self.user)
        self.assertFalse(notif.is_read)

        response = self.user_client.post(
            reverse('notification-read', args=[notif.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_as_read(self):
        """Отметка всех уведомлений как прочитанных."""
        self._create_notification(self.user, title='N1')
        self._create_notification(self.user, title='N2')
        self._create_notification(self.user, title='N3')

        response = self.user_client.post(reverse('notification-read-all'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_unread_count(self):
        """Подсчёт непрочитанных уведомлений."""
        self._create_notification(self.user)
        self._create_notification(self.user)
        n3 = self._create_notification(self.user)
        n3.is_read = True
        n3.save()

        response = self.user_client.get(reverse('notification-unread-count'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_submit_creates_notification_for_admins(self):
        """Подача KPI создаёт уведомление для руководителей."""
        value = KpiValue.objects.create(
            user=self.user, indicator=self.indicator,
            period='2025-01', actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_DRAFT
        )

        self.user_client.post(
            reverse('kpivalue-submit', args=[value.id]), {}, format='json'
        )

        admin_notifs = Notification.objects.filter(
            recipient=self.admin,
            notification_type=Notification.TYPE_SUBMITTED
        )
        self.assertEqual(admin_notifs.count(), 1)

    def test_approve_creates_notification_for_user(self):
        """Одобрение KPI создаёт уведомление для сотрудника."""
        value = KpiValue.objects.create(
            user=self.user, indicator=self.indicator,
            period='2025-02', actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_SUBMITTED
        )

        self.admin_client.post(
            reverse('kpivalue-approve', args=[value.id]),
            {'review_comment': 'OK'}, format='json'
        )

        user_notifs = Notification.objects.filter(
            recipient=self.user,
            notification_type=Notification.TYPE_APPROVED
        )
        self.assertEqual(user_notifs.count(), 1)

    def test_reject_creates_notification_for_user(self):
        """Отклонение KPI создаёт уведомление для сотрудника."""
        value = KpiValue.objects.create(
            user=self.user, indicator=self.indicator,
            period='2025-03', actual_value=5.0, target_value=10.0,
            status=KpiValue.STATUS_SUBMITTED
        )

        self.admin_client.post(
            reverse('kpivalue-reject', args=[value.id]),
            {'review_comment': 'Need more'}, format='json'
        )

        user_notifs = Notification.objects.filter(
            recipient=self.user,
            notification_type=Notification.TYPE_REJECTED
        )
        self.assertEqual(user_notifs.count(), 1)
        self.assertIn('Need more', user_notifs.first().message)

    def test_unauthenticated_cannot_access_notifications(self):
        """Неавторизованный пользователь не имеет доступа."""
        anon_client = APIClient()
        response = anon_client.get(reverse('notification-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
