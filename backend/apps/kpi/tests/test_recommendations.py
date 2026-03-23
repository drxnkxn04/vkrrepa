from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.kpi.models import KpiGroup, KpiIndicator, KpiRecommendation

User = get_user_model()


class RecommendationViewSetTestCase(APITestCase):
    """Тесты ViewSet рекомендаций."""

    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass12345')
        self.other_user = User.objects.create_user(username='user2', password='pass12345')

        group = KpiGroup.objects.create(name='Rec Group', weight=1.0, order=1)
        self.indicator = KpiIndicator.objects.create(
            group=group, name='Rec Indicator',
            max_value=10.0, weight=1.0, data_source='manual', order=1
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _create_recommendation(self, user, period='2025-01', is_completed=False, priority='high'):
        return KpiRecommendation.objects.create(
            user=user, indicator=self.indicator,
            period=period, text='Рекомендация тест',
            priority=priority,
            actual_value=3.0, target_value=10.0,
            current_completion=30.0,
            is_completed=is_completed,
        )

    def test_list_own_recommendations(self):
        """Пользователь видит только свои рекомендации."""
        self._create_recommendation(self.user)
        self._create_recommendation(self.other_user)

        response = self.client.get(reverse('recommendation-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)

    def test_filter_by_status_active(self):
        """Фильтрация: только активные рекомендации."""
        self._create_recommendation(self.user, period='2025-01', is_completed=False)
        self._create_recommendation(self.user, period='2025-02', is_completed=True)

        response = self.client.get(
            reverse('recommendation-list'), {'status': 'active'}
        )
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)

    def test_filter_by_status_completed(self):
        """Фильтрация: только выполненные рекомендации."""
        self._create_recommendation(self.user, period='2025-03', is_completed=False)
        self._create_recommendation(self.user, period='2025-04', is_completed=True)

        response = self.client.get(
            reverse('recommendation-list'), {'status': 'completed'}
        )
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)

    def test_filter_by_period(self):
        """Фильтрация по периоду."""
        self._create_recommendation(self.user, period='2025-05')
        self._create_recommendation(self.user, period='2025-06')

        response = self.client.get(
            reverse('recommendation-list'), {'period': '2025-05'}
        )
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)

    def test_mark_as_complete(self):
        """Отметка рекомендации как выполненной."""
        rec = self._create_recommendation(self.user, period='2025-07')

        response = self.client.post(
            reverse('recommendation-complete', args=[rec.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rec.refresh_from_db()
        self.assertTrue(rec.is_completed)

    def test_mark_as_uncomplete(self):
        """Возврат рекомендации в активные."""
        rec = self._create_recommendation(self.user, period='2025-08', is_completed=True)

        response = self.client.post(
            reverse('recommendation-uncomplete', args=[rec.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        rec.refresh_from_db()
        self.assertFalse(rec.is_completed)

    def test_cannot_access_other_user_recommendation(self):
        """Пользователь не может управлять чужими рекомендациями."""
        rec = self._create_recommendation(self.other_user, period='2025-09')

        response = self.client.post(
            reverse('recommendation-complete', args=[rec.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
