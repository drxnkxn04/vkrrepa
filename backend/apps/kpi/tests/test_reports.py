from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue

User = get_user_model()


class ReportsTestCase(APITestCase):
    """Тесты генерации отчётов (PDF и Excel)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='employee', password='pass12345',
            first_name='Иван', last_name='Петров'
        )
        self.admin = User.objects.create_user(
            username='manager', password='pass12345', is_staff=True
        )

        group = KpiGroup.objects.create(name='Report Group', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group, name='Report Indicator',
            max_value=10.0, weight=1.0, data_source='manual', order=1
        )

        KpiValue.objects.create(
            user=self.user, indicator=self.indicator,
            period='2025-01', actual_value=7.0, target_value=10.0,
            status=KpiValue.STATUS_APPROVED, is_verified=True
        )

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def test_generate_pdf_report(self):
        """Генерация PDF-отчёта для текущего пользователя."""
        response = self.user_client.get(
            reverse('generate-report'), {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', response['Content-Type'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_generate_pdf_without_period(self):
        """Генерация PDF без периода — ошибка."""
        response = self.user_client.get(reverse('generate-report'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_excel_report(self):
        """Генерация Excel-отчёта для текущего пользователя."""
        response = self.user_client.get(
            reverse('generate-excel-report'), {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_generate_excel_without_period(self):
        """Генерация Excel без периода — ошибка."""
        response = self.user_client.get(reverse('generate-excel-report'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_generate_pdf_for_user(self):
        """Руководитель генерирует PDF-отчёт за сотрудника."""
        response = self.admin_client.get(
            reverse('generate-user-report', args=[self.user.id]),
            {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', response['Content-Type'])

    def test_admin_generate_excel_for_user(self):
        """Руководитель генерирует Excel-отчёт за сотрудника."""
        response = self.admin_client.get(
            reverse('generate-user-excel-report', args=[self.user.id]),
            {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('spreadsheetml', response['Content-Type'])

    def test_admin_report_for_nonexistent_user(self):
        """Отчёт за несуществующего пользователя — 404."""
        response = self.admin_client.get(
            reverse('generate-user-report', args=[9999]),
            {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_generate_report_for_other(self):
        """Обычный пользователь не может генерировать отчёт за другого."""
        response = self.user_client.get(
            reverse('generate-user-report', args=[self.admin.id]),
            {'period': '2025-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
