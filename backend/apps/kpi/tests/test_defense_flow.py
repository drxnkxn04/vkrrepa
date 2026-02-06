from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue

User = get_user_model()


class DefenseFlowAPITestCase(APITestCase):
    def setUp(self):
        self.employee_password = 'pass12345'
        self.manager_password = 'pass12345'

        self.employee = User.objects.create_user(
            username='flow_employee',
            email='flow_employee@example.com',
            password=self.employee_password,
        )
        self.manager = User.objects.create_user(
            username='flow_manager',
            email='flow_manager@example.com',
            password=self.manager_password,
            is_staff=True,
        )

        group = KpiGroup.objects.create(name='Flow Group', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group,
            name='Flow Indicator',
            max_value=10.0,
            weight=1.0,
            data_source='manual',
            order=1,
        )
        self.period = timezone.now().strftime('%Y-%m')

    def _auth_client(self, username: str, password: str):
        token_response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': username, 'password': password},
            format='json',
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        token = token_response.data['access']

        authed_client = self.client_class()
        authed_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return authed_client

    def test_employee_to_manager_full_flow(self):
        employee_client = self._auth_client(self.employee.username, self.employee_password)

        create_response = employee_client.post(
            reverse('kpivalue-list'),
            {
                'indicator_id': self.indicator.id,
                'period': self.period,
                'actual_value': 7.0,
                'target_value': 10.0,
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        value_id = create_response.data['id']
        self.assertEqual(create_response.data['status'], KpiValue.STATUS_DRAFT)

        submit_response = employee_client.post(
            reverse('kpivalue-submit', args=[value_id]),
            {},
            format='json',
        )
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(submit_response.data['status'], KpiValue.STATUS_SUBMITTED)

        manager_client = self._auth_client(self.manager.username, self.manager_password)

        pending_response = manager_client.get(reverse('kpivalue-pending'))
        self.assertEqual(pending_response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == value_id for item in pending_response.data))

        approve_response = manager_client.post(
            reverse('kpivalue-approve', args=[value_id]),
            {'review_comment': 'Approved in defense flow test'},
            format='json',
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_response.data['status'], KpiValue.STATUS_APPROVED)
        self.assertTrue(approve_response.data['is_verified'])

        dashboard_response = employee_client.get(
            reverse('kpivalue-dashboard'),
            {'period': self.period},
        )
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertGreater(dashboard_response.data['total_score'], 0.0)

        report_response = employee_client.get(
            reverse('generate-report'),
            {'period': self.period},
        )
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)
        self.assertIn('application/pdf', report_response['Content-Type'])
        self.assertTrue(report_response.content.startswith(b'%PDF'))
