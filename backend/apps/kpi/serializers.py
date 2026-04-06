from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import KpiGroup, KpiIndicator, KpiValue, KpiValueLog, KpiRecommendation, Notification, KpiTarget

User = get_user_model()


class KpiIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiIndicator
        fields = '__all__'


class KpiGroupSerializer(serializers.ModelSerializer):
    indicators = KpiIndicatorSerializer(many=True, read_only=True)

    class Meta:
        model = KpiGroup
        fields = '__all__'


class KpiValueSerializer(serializers.ModelSerializer):
    indicator = KpiIndicatorSerializer(read_only=True)
    indicator_id = serializers.PrimaryKeyRelatedField(
        queryset=KpiIndicator.objects.all(),
        source='indicator',
        write_only=True
    )
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.SerializerMethodField()
    target_value = serializers.SerializerMethodField()

    class Meta:
        model = KpiValue
        fields = '__all__'
        read_only_fields = (
            'user',
            'created_at',
            'updated_at',
            'is_verified',
            'status',
            'submitted_at',
            'reviewer',
            'reviewed_at',
        )

    def _get_targets_cache(self):
        """Кэш KpiTarget на время сериализации (избегаем N+1 запросов)."""
        if '_targets_cache' not in self.context:
            targets = KpiTarget.objects.all().values_list(
                'user_id', 'indicator_id', 'period', 'target_value',
            )
            self.context['_targets_cache'] = {
                (uid, iid, p): tv for uid, iid, p, tv in targets
            }
        return self.context['_targets_cache']

    def get_target_value(self, obj):
        """Если target_value == 0, подставляем из KpiTarget или indicator.max_value."""
        if obj.target_value and obj.target_value > 0:
            return obj.target_value
        # Индивидуальный план (из кэша)
        cache = self._get_targets_cache()
        cached_tv = cache.get((obj.user_id, obj.indicator_id, obj.period))
        if cached_tv is not None:
            return float(cached_tv)
        # Значение из индикатора
        if obj.indicator and obj.indicator.max_value > 0:
            return float(obj.indicator.max_value)
        return 0.0

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'email': obj.user.email,
        }


class KpiValueLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = KpiValueLog
        fields = [
            'id', 'action', 'action_display', 'actor', 'actor_name',
            'comment', 'old_value', 'new_value', 'created_at',
        ]

    def get_actor_name(self, obj):
        if not obj.actor:
            return None
        return obj.actor.get_full_name() or obj.actor.username

    def get_action_display(self, obj):
        return obj.get_action_display()


class KpiRecommendationSerializer(serializers.ModelSerializer):
    indicator = KpiIndicatorSerializer(read_only=True)
    indicator_id = serializers.PrimaryKeyRelatedField(
        queryset=KpiIndicator.objects.all(),
        source='indicator',
        write_only=True
    )

    class Meta:
        model = KpiRecommendation
        fields = '__all__'
        read_only_fields = ('user', 'created_at')


class KpiTargetSerializer(serializers.ModelSerializer):
    indicator = KpiIndicatorSerializer(read_only=True)
    indicator_id = serializers.PrimaryKeyRelatedField(
        queryset=KpiIndicator.objects.all(),
        source='indicator',
        write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    user_name = serializers.SerializerMethodField()
    set_by_name = serializers.SerializerMethodField()

    class Meta:
        model = KpiTarget
        fields = [
            'id', 'user', 'user_id', 'user_name', 'indicator', 'indicator_id',
            'period', 'target_value', 'set_by', 'set_by_name', 'comment',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('user', 'set_by', 'created_at', 'updated_at')

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_set_by_name(self, obj):
        if not obj.set_by:
            return None
        return obj.set_by.get_full_name() or obj.set_by.username


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'kpi_value_id', 'is_read', 'created_at']
        read_only_fields = ['notification_type', 'title', 'message', 'kpi_value_id', 'created_at']
