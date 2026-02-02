from rest_framework import serializers
from .models import KpiGroup, KpiIndicator, KpiValue, KpiRecommendation


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

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'full_name': obj.user.get_full_name(),
            'email': obj.user.email,
        }


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
