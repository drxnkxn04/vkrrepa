from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Добавляем кастомные поля в токен
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        token['email'] = user.email
        token['full_name'] = user.get_full_name()

        return token