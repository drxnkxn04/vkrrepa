from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue

User = get_user_model()


class KpiWorkflowAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='pass12345'
        )
        self.other_user = User.objects.create_user(
            username='employee2',
            email='employee2@example.com',
            password='pass12345'
        )
        self.admin = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass12345',
            is_staff=True
        )

        group = KpiGroup.objects.create(name='Publications', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group,
            name='Journal papers',
            max_value=10.0,
            weight=1.0,
            data_source='manual',
            order=1
        )

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.other_user_client = APIClient()
        self.other_user_client.force_authenticate(user=self.other_user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def _create_value(self, client, period='2025-01', actual_value=5.0):
        response = client.post(
            reverse('kpivalue-list'),
            {
                'indicator_id': self.indicator.id,
                'period': period,
                'actual_value': actual_value,
                'target_value': 10.0,
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def _submit_value(self, value_id):
        response = self.user_client.post(
            reverse('kpivalue-submit', args=[value_id]),
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def test_user_can_submit_own_value(self):
        created = self._create_value(self.user_client, period='2025-01')

        response = self.user_client.post(
            reverse('kpivalue-submit', args=[created['id']]),
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], KpiValue.STATUS_SUBMITTED)
        self.assertIsNotNone(response.data['submitted_at'])

    def test_user_cannot_submit_other_user_value(self):
        created = self._create_value(self.user_client, period='2025-02')

        response = self.other_user_client.post(
            reverse('kpivalue-submit', args=[created['id']]),
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_approve_submitted_value(self):
        created = self._create_value(self.user_client, period='2025-03')
        self._submit_value(created['id'])

        response = self.admin_client.post(
            reverse('kpivalue-approve', args=[created['id']]),
            {'review_comment': 'Looks good'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], KpiValue.STATUS_APPROVED)
        self.assertTrue(response.data['is_verified'])
        self.assertEqual(response.data['reviewer'], self.admin.id)
        self.assertEqual(response.data['review_comment'], 'Looks good')

    def test_admin_can_reject_submitted_value(self):
        created = self._create_value(self.user_client, period='2025-04')
        self._submit_value(created['id'])

        response = self.admin_client.post(
            reverse('kpivalue-reject', args=[created['id']]),
            {'review_comment': 'Need evidence'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], KpiValue.STATUS_REJECTED)
        self.assertFalse(response.data['is_verified'])
        self.assertEqual(response.data['reviewer'], self.admin.id)
        self.assertEqual(response.data['review_comment'], 'Need evidence')

    def test_non_admin_cannot_approve(self):
        created = self._create_value(self.user_client, period='2025-05')
        self._submit_value(created['id'])

        response = self.other_user_client.post(
            reverse('kpivalue-approve', args=[created['id']]),
            {'review_comment': 'Trying to approve'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_approve_non_submitted_value(self):
        created = self._create_value(self.user_client, period='2025-06')

        response = self.admin_client.post(
            reverse('kpivalue-approve', args=[created['id']]),
            {'review_comment': 'Trying to approve draft'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pending_requires_admin_and_returns_only_submitted(self):
        submitted_value = self._create_value(self.user_client, period='2025-07')
        self._submit_value(submitted_value['id'])
        self._create_value(self.user_client, period='2025-08')

        user_response = self.user_client.get(reverse('kpivalue-pending'))
        self.assertEqual(user_response.status_code, status.HTTP_403_FORBIDDEN)

        admin_response = self.admin_client.get(reverse('kpivalue-pending'))
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admin_response.data), 1)
        self.assertEqual(admin_response.data[0]['id'], submitted_value['id'])

    def test_pending_can_be_filtered_by_period(self):
        value_p1 = self._create_value(self.user_client, period='2025-09')
        self._submit_value(value_p1['id'])

        value_p2 = self._create_value(self.user_client, period='2025-10')
        self._submit_value(value_p2['id'])

        filtered = self.admin_client.get(
            reverse('kpivalue-pending'),
            {'period': '2025-09'}
        )

        self.assertEqual(filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(filtered.data), 1)
        self.assertEqual(filtered.data[0]['period'], '2025-09')

    def test_periods_scope_for_user_and_admin(self):
        KpiValue.objects.create(
            user=self.user,
            indicator=self.indicator,
            period='2025-01',
            actual_value=5.0,
            target_value=10.0,
            status=KpiValue.STATUS_APPROVED,
            is_verified=True
        )
        KpiValue.objects.create(
            user=self.other_user,
            indicator=self.indicator,
            period='2025-02',
            actual_value=6.0,
            target_value=10.0,
            status=KpiValue.STATUS_APPROVED,
            is_verified=True
        )
        KpiValue.objects.create(
            user=self.other_user,
            indicator=self.indicator,
            period='2025-03',
            actual_value=3.0,
            target_value=10.0,
            status=KpiValue.STATUS_DRAFT,
            is_verified=False
        )

        user_periods = self.user_client.get(reverse('kpivalue-periods'))
        self.assertEqual(user_periods.status_code, status.HTTP_200_OK)
        self.assertEqual(user_periods.data, ['2025-01'])

        admin_periods = self.admin_client.get(reverse('kpivalue-periods'))
        self.assertEqual(admin_periods.status_code, status.HTTP_200_OK)
        # Руководитель видит все периоды в системе, включая черновики
        self.assertEqual(admin_periods.data, ['2025-03', '2025-02', '2025-01'])

    def test_values_list_can_be_filtered_by_period(self):
        KpiValue.objects.create(
            user=self.user,
            indicator=self.indicator,
            period='2025-11',
            actual_value=1.0,
            target_value=10.0,
            status=KpiValue.STATUS_DRAFT,
            is_verified=False
        )
        KpiValue.objects.create(
            user=self.user,
            indicator=self.indicator,
            period='2025-12',
            actual_value=2.0,
            target_value=10.0,
            status=KpiValue.STATUS_DRAFT,
            is_verified=False
        )

        response = self.user_client.get(reverse('kpivalue-list'), {'period': '2025-11'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['period'], '2025-11')

    def test_admin_can_generate_report_for_selected_user(self):
        response = self.admin_client.get(
            reverse('generate-user-report', args=[self.user.id]),
            {'period': '2025-01'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', response['Content-Type'])
