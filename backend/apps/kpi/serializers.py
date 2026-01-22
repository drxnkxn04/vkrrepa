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

    class Meta:
        model = KpiValue
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


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