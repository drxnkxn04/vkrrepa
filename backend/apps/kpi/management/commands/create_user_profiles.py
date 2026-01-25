# backend/apps/kpi/management/commands/create_user_profiles.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.kpi.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает профили для всех пользователей без профиля'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        count = 0

        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Создан профиль для {user.username}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Всего создано профилей: {count}')
        )