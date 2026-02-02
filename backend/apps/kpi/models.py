from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KpiGroup(models.Model):
    """Группы показателей KPI"""
    name = models.CharField(max_length=100, verbose_name='Название группы')
    description = models.TextField(blank=True, verbose_name='Описание')
    weight = models.FloatField(default=0.0, verbose_name='Вес в итоговой оценке')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')

    class Meta:
        ordering = ['order']
        verbose_name = 'Группа KPI'
        verbose_name_plural = 'Группы KPI'

    def __str__(self):
        return self.name


class KpiIndicator(models.Model):
    """Отдельные показатели KPI"""
    DATA_SOURCE_CHOICES = (
        ('api', 'Автоматический сбор (API)'),
        ('manual', 'Ручной ввод'),
        ('import', 'Импорт из систем'),
    )

    group = models.ForeignKey(KpiGroup, on_delete=models.CASCADE, related_name='indicators')
    name = models.CharField(max_length=200, verbose_name='Название показателя')
    description = models.TextField(blank=True, verbose_name='Описание')
    formula = models.TextField(blank=True, verbose_name='Формула расчета')
    data_source = models.CharField(max_length=20, choices=DATA_SOURCE_CHOICES, default='manual')
    max_value = models.FloatField(default=0.0, verbose_name='Максимальное значение (план)')
    unit = models.CharField(max_length=50, blank=True, verbose_name='Единица измерения')
    weight = models.FloatField(default=1.0, verbose_name='Вес показателя')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')

    class Meta:
        ordering = ['group__order', 'order']
        verbose_name = 'Показатель KPI'
        verbose_name_plural = 'Показатели KPI'

    def __str__(self):
        return f"{self.group.name}: {self.name}"


class KpiValue(models.Model):
    """KPI value workflow data"""
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    )

    """Значения KPI для пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kpi_values')
    indicator = models.ForeignKey(KpiIndicator, on_delete=models.CASCADE)
    period = models.CharField(max_length=7, verbose_name='Период (ГГГГ-ММ)')  # YYYY-MM
    actual_value = models.FloatField(default=0.0, verbose_name='Фактическое значение')
    target_value = models.FloatField(default=0.0, verbose_name='Плановое значение')
    is_verified = models.BooleanField(default=False, verbose_name='Подтверждено')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name='Status'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kpi_values'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)
    evidence = models.FileField(upload_to='evidence/%Y/%m/', blank=True, null=True,
                                verbose_name='Подтверждающий документ')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'indicator', 'period')
        verbose_name = 'Значение KPI'
        verbose_name_plural = 'Значения KPI'

    def __str__(self):
        return f"{self.user} - {self.indicator} ({self.period})"


class KpiRecommendation(models.Model):
    """Рекомендации по улучшению KPI"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    indicator = models.ForeignKey(KpiIndicator, on_delete=models.CASCADE, verbose_name='Показатель')
    period = models.CharField(max_length=7, verbose_name='Период (ГГГГ-ММ)')  # YYYY-MM
    text = models.TextField(verbose_name='Текст рекомендации')
    target_value = models.FloatField(default=0.0, verbose_name='Целевое значение')
    deadline_period = models.CharField(max_length=7, null=True, blank=True, verbose_name='Срок выполнения')
    is_completed = models.BooleanField(default=False, verbose_name='Выполнено')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рекомендация KPI'
        verbose_name_plural = 'Рекомендации KPI'

    def __str__(self):
        return f"{self.user} - {self.indicator} ({self.period})"


class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    orcid = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='ORCID идентификатор'
    )
    department = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Подразделение'
    )
    position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Должность'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.username}"