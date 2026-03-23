# backend/apps/kpi/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile, KpiValue

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль при создании пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=KpiValue)
@receiver(post_delete, sender=KpiValue)
def invalidate_kpi_cache(sender, instance, **kwargs):
    """Сбрасывает кэш дашборда при изменении KPI-значений."""
    from .services.kpi_calculator import KpiCalculator
    KpiCalculator.invalidate_cache(instance.user_id, instance.period)