# backend/apps/kpi/crossref_integration.py

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime
import logging

from ..models import KpiIndicator, KpiValue
from ...integrations.services.crossref_service import CrossrefAPIService

User = get_user_model()
logger = logging.getLogger(__name__)


class CrossrefKpiIntegration:
    """
    Интеграция Crossref API с системой KPI.
    Автоматический сбор публикаций и обновление показателей KPI.
    """

    def __init__(self):
        self.crossref_service = CrossrefAPIService()

    def sync_user_publications(self, user_id: int, orcid: str, year: int = None) -> dict:
        """
        Синхронизация публикаций пользователя из Crossref.

        Args:
            user_id: ID пользователя в системе
            orcid: ORCID идентификатор исследователя
            year: Год для фильтрации публикаций (если None, берутся все)

        Returns:
            Dict со статистикой синхронизации
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            return {'success': False, 'error': 'User not found'}

        # Получаем публикации из Crossref
        try:
            publications = self.crossref_service.get_publications_by_orcid(orcid, year)
        except Exception as e:
            logger.error(f"Ошибка получения данных из Crossref для ORCID {orcid}: {str(e)}")
            return {'success': False, 'error': str(e)}

        if not publications:
            logger.warning(f"Публикации для ORCID {orcid} не найдены")
            return {'success': True, 'publications_count': 0, 'kpi_updated': 0}

        # Обновляем KPI на основе публикаций
        stats = self._update_kpi_from_publications(user, publications)

        logger.info(f"Синхронизация завершена для {user.username}. "
                    f"Найдено публикаций: {len(publications)}, "
                    f"Обновлено KPI: {stats['kpi_updated']}")

        return {
            'success': True,
            'publications_count': len(publications),
            'kpi_updated': stats['kpi_updated'],
            'publications': publications[:5]  # Первые 5 для отображения
        }

    @transaction.atomic
    def _update_kpi_from_publications(self, user: User, publications: list) -> dict:
        """
        Обновление показателей KPI на основе полученных публикаций.

        Args:
            user: Объект пользователя
            publications: Список публикаций из Crossref

        Returns:
            Dict со статистикой обновлений
        """
        kpi_updated = 0

        # Группируем публикации по годам
        publications_by_year = {}
        for pub in publications:
            year = pub.get('year')
            if year:
                if year not in publications_by_year:
                    publications_by_year[year] = []
                publications_by_year[year].append(pub)

        # Находим индикаторы для публикаций
        publication_indicators = self._get_publication_indicators()

        for year, year_publications in publications_by_year.items():
            # Формируем период в формате YYYY-MM (используем январь как базовый месяц года)
            period = f"{year}-01"

            # Обновляем различные типы показателей
            for indicator in publication_indicators:
                indicator_name_lower = indicator.name.lower()

                # Общее количество публикаций
                if 'публикаций' in indicator_name_lower and 'общее' in indicator_name_lower:
                    value = len(year_publications)
                    self._update_or_create_kpi_value(
                        user, indicator, period, value, indicator.max_value
                    )
                    kpi_updated += 1

                # Публикации в Scopus/WoS
                elif 'scopus' in indicator_name_lower or 'wos' in indicator_name_lower:
                    # Фильтруем журнальные статьи (обычно индексируются в Scopus/WoS)
                    scopus_publications = [
                        p for p in year_publications
                        if p['type'] == 'journal-article'
                    ]
                    value = len(scopus_publications)
                    self._update_or_create_kpi_value(
                        user, indicator, period, value, indicator.max_value
                    )
                    kpi_updated += 1

                # Публикации ВАК
                elif 'вак' in indicator_name_lower:
                    # Для ВАК используем российские журналы
                    vak_publications = [
                        p for p in year_publications
                        if self._is_russian_journal(p.get('journal', ''))
                    ]
                    value = len(vak_publications)
                    self._update_or_create_kpi_value(
                        user, indicator, period, value, indicator.max_value
                    )
                    kpi_updated += 1

                # Конференционные публикации
                elif 'конференц' in indicator_name_lower:
                    conference_publications = [
                        p for p in year_publications
                        if p['type'] == 'proceedings-article'
                    ]
                    value = len(conference_publications)
                    self._update_or_create_kpi_value(
                        user, indicator, period, value, indicator.max_value
                    )
                    kpi_updated += 1

        return {'kpi_updated': kpi_updated}

    def _get_publication_indicators(self):
        """
        Получение списка индикаторов, связанных с публикациями.
        """
        return KpiIndicator.objects.filter(
            data_source='api',
            name__icontains='публикаци'
        )

    def _update_or_create_kpi_value(
            self,
            user: User,
            indicator: KpiIndicator,
            period: str,
            actual_value: float,
            target_value: float
    ):
        """
        Создание или обновление значения KPI.
        """
        KpiValue.objects.update_or_create(
            user=user,
            indicator=indicator,
            period=period,
            defaults={
                'actual_value': actual_value,
                'target_value': target_value,
                'is_verified': True,
                'status': KpiValue.STATUS_APPROVED,  # Данные из API считаем верифицированными
                'comment': f'Автоматически обновлено из Crossref API {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            }
        )

    def _is_russian_journal(self, journal_name: str) -> bool:
        """
        Простая эвристика для определения российских журналов.
        """
        # Список ключевых слов российских журналов
        russian_keywords = [
            'russian', 'российский', 'moscow', 'moscow', 'petersburg',
            'вестник', 'известия', 'журнал', 'наука'
        ]

        journal_lower = journal_name.lower()
        return any(keyword in journal_lower for keyword in russian_keywords)

    def sync_all_users_publications(self, year: int = None) -> dict:
        """
        Массовая синхронизация публикаций для всех пользователей с ORCID.
        Используется в Celery задачах.

        Args:
            year: Год для фильтрации (если None, синхронизируется текущий год)

        Returns:
            Dict со статистикой по всем пользователям
        """
        if year is None:
            year = datetime.now().year

        # Предполагается, что ORCID хранится в профиле пользователя
        # Если у вас другая структура, измените запрос
        users_with_orcid = User.objects.filter(
            is_active=True,
            profile__orcid__isnull=False  # Предполагаем связь с моделью профиля
        ).exclude(profile__orcid='')

        stats = {
            'total_users': users_with_orcid.count(),
            'success_count': 0,
            'error_count': 0,
            'total_publications': 0,
            'total_kpi_updated': 0
        }

        for user in users_with_orcid:
            try:
                orcid = user.profile.orcid
                result = self.sync_user_publications(user.id, orcid, year)

                if result['success']:
                    stats['success_count'] += 1
                    stats['total_publications'] += result['publications_count']
                    stats['total_kpi_updated'] += result['kpi_updated']
                else:
                    stats['error_count'] += 1

            except Exception as e:
                logger.error(f"Ошибка синхронизации для пользователя {user.username}: {str(e)}")
                stats['error_count'] += 1

        logger.info(f"Массовая синхронизация завершена. "
                    f"Обработано: {stats['total_users']}, "
                    f"Успешно: {stats['success_count']}, "
                    f"Ошибок: {stats['error_count']}")

        return stats


# Пример использования в представлении Django
class CrossrefSyncView:
    """
    Пример представления для синхронизации публикаций через API.
    """

    def sync_my_publications(self, request):
        """
        Синхронизация публикаций текущего пользователя.
        """
        user = request.user

        # Предполагается, что ORCID хранится в профиле
        if not hasattr(user, 'profile') or not user.profile.orcid:
            return {
                'success': False,
                'error': 'ORCID не указан в профиле пользователя'
            }

        integrator = CrossrefKpiIntegration()
        result = integrator.sync_user_publications(
            user_id=user.id,
            orcid=user.profile.orcid,
            year=datetime.now().year
        )

        return result