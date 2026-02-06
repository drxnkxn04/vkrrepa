from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.kpi.models import KpiGroup, KpiIndicator, KpiValue

User = get_user_model()


class Command(BaseCommand):
    help = 'Prepare deterministic demo data for employee->manager KPI workflow.'

    def handle(self, *args, **options):
        employee, _ = User.objects.get_or_create(
            username='demo_employee',
            defaults={
                'email': 'demo_employee@example.com',
                'first_name': 'Demo',
                'last_name': 'Employee',
                'is_active': True,
            },
        )
        employee.set_password('demo12345')
        employee.save(update_fields=['password'])

        manager, _ = User.objects.get_or_create(
            username='demo_manager',
            defaults={
                'email': 'demo_manager@example.com',
                'first_name': 'Demo',
                'last_name': 'Manager',
                'is_active': True,
                'is_staff': True,
            },
        )
        manager.is_staff = True
        manager.set_password('demo12345')
        manager.save(update_fields=['is_staff', 'password'])

        group, _ = KpiGroup.objects.get_or_create(
            name='Demo KPI Group',
            defaults={
                'description': 'Demo group for defense workflow',
                'weight': 1.0,
                'order': 1,
            },
        )

        indicator_a, _ = KpiIndicator.objects.get_or_create(
            group=group,
            name='Demo Publications',
            defaults={
                'description': 'Manual demo indicator',
                'data_source': 'manual',
                'max_value': 10.0,
                'unit': 'items',
                'weight': 1.0,
                'order': 1,
            },
        )
        indicator_b, _ = KpiIndicator.objects.get_or_create(
            group=group,
            name='Demo Reports',
            defaults={
                'description': 'Manual demo indicator',
                'data_source': 'manual',
                'max_value': 6.0,
                'unit': 'items',
                'weight': 1.0,
                'order': 2,
            },
        )

        current_period = timezone.now().strftime('%Y-%m')
        previous_period = self._previous_period()

        KpiValue.objects.update_or_create(
            user=employee,
            indicator=indicator_a,
            period=current_period,
            defaults={
                'actual_value': 3.0,
                'target_value': 10.0,
                'status': KpiValue.STATUS_DRAFT,
                'is_verified': False,
                'reviewer': None,
                'reviewed_at': None,
                'submitted_at': None,
                'review_comment': '',
                'comment': 'Draft value for submit demo',
            },
        )
        KpiValue.objects.update_or_create(
            user=employee,
            indicator=indicator_b,
            period=current_period,
            defaults={
                'actual_value': 4.0,
                'target_value': 6.0,
                'status': KpiValue.STATUS_SUBMITTED,
                'is_verified': False,
                'submitted_at': timezone.now(),
                'reviewer': None,
                'reviewed_at': None,
                'review_comment': '',
                'comment': 'Submitted value for manager approval demo',
            },
        )
        KpiValue.objects.update_or_create(
            user=employee,
            indicator=indicator_a,
            period=previous_period,
            defaults={
                'actual_value': 8.0,
                'target_value': 10.0,
                'status': KpiValue.STATUS_APPROVED,
                'is_verified': True,
                'reviewer': manager,
                'submitted_at': timezone.now(),
                'reviewed_at': timezone.now(),
                'review_comment': 'Baseline approved value',
                'comment': 'Approved baseline for charts',
            },
        )

        self.stdout.write(self.style.SUCCESS('Demo workflow data is ready.'))
        self.stdout.write('Employee login: demo_employee / demo12345')
        self.stdout.write('Manager login: demo_manager / demo12345')
        self.stdout.write(f'Current period: {current_period}')

    def _previous_period(self) -> str:
        now = timezone.now()
        year = now.year
        month = now.month - 1
        if month == 0:
            year -= 1
            month = 12
        return f'{year}-{month:02d}'
