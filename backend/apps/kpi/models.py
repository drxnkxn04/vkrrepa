from django.core import validators
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KpiGroup(models.Model):
    """Группы показателей KPI"""
    ROLE_PPS = 'pps'
    ROLE_ROP = 'rop'

    ROLE_CHOICES = (
        (ROLE_PPS, 'ППС (преподаватель)'),
        (ROLE_ROP, 'РОП (руководитель)'),
    )

    name = models.CharField(max_length=100, verbose_name='Название группы')
    description = models.TextField(blank=True, verbose_name='Описание')
    weight = models.FloatField(default=0.0, verbose_name='Вес в итоговой оценке')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default=ROLE_PPS,
        verbose_name='Роль'
    )
    max_points = models.FloatField(default=0.0, verbose_name='Максимум баллов по группе')
    min_threshold = models.FloatField(default=0.0, verbose_name='Минимальный порог (баллы)')

    class Meta:
        ordering = ['role', 'order']
        verbose_name = 'Группа KPI'
        verbose_name_plural = 'Группы KPI'

    def __str__(self):
        return f"[{self.get_role_display()}] {self.name}"


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
    max_points = models.FloatField(default=0.0, verbose_name='Максимум баллов')
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
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, 'Высокий'),
        (PRIORITY_MEDIUM, 'Средний'),
        (PRIORITY_LOW, 'Низкий'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    indicator = models.ForeignKey(KpiIndicator, on_delete=models.CASCADE, verbose_name='Показатель')
    period = models.CharField(max_length=7, verbose_name='Период (ГГГГ-ММ)')  # YYYY-MM
    text = models.TextField(verbose_name='Текст рекомендации')
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM,
        verbose_name='Приоритет'
    )
    actual_value = models.FloatField(default=0.0, verbose_name='Фактическое значение')
    target_value = models.FloatField(default=0.0, verbose_name='Целевое значение')
    current_completion = models.FloatField(default=0.0, verbose_name='Процент выполнения')
    deadline_period = models.CharField(max_length=7, null=True, blank=True, verbose_name='Срок выполнения')
    is_completed = models.BooleanField(default=False, verbose_name='Выполнено')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Рекомендация KPI'
        verbose_name_plural = 'Рекомендации KPI'
        ordering = ['priority', '-current_completion']

    def __str__(self):
        return f"{self.user} - {self.indicator} ({self.period})"


class Notification(models.Model):
    """Уведомления для пользователей"""
    TYPE_SUBMITTED = 'submitted'
    TYPE_APPROVED = 'approved'
    TYPE_REJECTED = 'rejected'

    TYPE_CHOICES = (
        (TYPE_SUBMITTED, 'KPI подан на проверку'),
        (TYPE_APPROVED, 'KPI одобрен'),
        (TYPE_REJECTED, 'KPI отклонён'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    kpi_value = models.ForeignKey(
        'KpiValue', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return f"{self.recipient} - {self.title}"


class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    ROLE_PPS = 'pps'
    ROLE_ROP = 'rop'

    ROLE_CHOICES = (
        (ROLE_PPS, 'ППС (преподаватель)'),
        (ROLE_ROP, 'РОП (руководитель)'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default=ROLE_PPS,
        verbose_name='Роль в системе KPI'
    )
    orcid = models.CharField(
        max_length=19,
        blank=True,
        null=True,
        verbose_name='ORCID идентификатор',
        validators=[
            validators.RegexValidator(
                regex=r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$',
                message='Неверный формат ORCID. Ожидается: 0000-0000-0000-0000'
            )
        ]
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

    def save(self, *args, **kwargs):
        if self.orcid:
            self.orcid = self.orcid.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Профиль {self.user.username}"


def get_user_kpi_role(user) -> str:
    """
    Определяет KPI-роль пользователя.
    is_staff → РОП, обычный пользователь → ППС.
    Если в профиле явно выбрана роль РОП для обычного пользователя — уважаем выбор.
    """
    profile = getattr(user, 'profile', None)
    if user.is_staff:
        # Руководитель — всегда РОП
        return KpiGroup.ROLE_ROP
    if profile and profile.role:
        return profile.role
    return KpiGroup.ROLE_PPS
