# backend/apps/kpi/api/crossref_views.py

print("=" * 80)
print(" ЗАГРУЖЕН ФАЙЛ: backend/apps/kpi/api/crossref_views.py")
print("=" * 80)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
import logging

from apps.integrations.services.crossref_service import (
    CrossrefAPIService,
    CrossrefAPIError,
    CrossrefTimeoutError,
    CrossrefConnectionError,
    CrossrefRateLimitError
)
from apps.kpi.models import KpiIndicator, KpiValue

logger = logging.getLogger(__name__)


class CrossrefSyncView(APIView):
    """
    Синхронизация публикаций из Crossref API с автоматическим сохранением в KPI.

    POST /api/kpi/crossref/sync/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        orcid = request.data.get('orcid')
        year = request.data.get('year')
        save_to_kpi = request.data.get('save_to_kpi', True)

        logger.info("=" * 80)
        logger.info(f" ВЫЗВАН CrossrefSyncView.post() для {user.username}")
        logger.info("=" * 80)

        # Валидация ORCID
        if not orcid:
            if hasattr(user, 'profile') and user.profile.orcid:
                orcid = user.profile.orcid
            else:
                return Response(
                    {'success': False, 'error': 'ORCID не указан'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            crossref_service = CrossrefAPIService()

            logger.info(f" Начало синхронизации для {user.username} с ORCID {orcid}")

            # Получаем публикации из Crossref
            publications = crossref_service.get_publications_by_orcid(
                orcid=orcid,
                year=year,
                max_results=100
            )

            logger.info(f" Найдено {len(publications)} публикаций")

            # Сохраняем в KPI
            saved_count = 0
            skipped_count = 0
            errors = []

            if save_to_kpi and publications:
                logger.info(f" Начинаем сохранение в KPI...")
                saved_count, skipped_count, errors = self._save_publications_to_kpi(
                    user=user,
                    publications=publications
                )

            logger.info(f"✅ ИТОГО: saved={saved_count}, skipped={skipped_count}, errors={len(errors)}")

            return Response({
                'success': True,
                'publications_count': len(publications),
                'saved_to_kpi': saved_count,
                'skipped': skipped_count,
                'errors': errors,
                'publications': publications,
                'orcid': orcid,
                'year': year
            })

        except Exception as e:
            logger.exception(f" Ошибка: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _save_publications_to_kpi(self, user, publications):
        """Сохранение публикаций в KPI."""
        saved_count = 0
        skipped_count = 0
        errors = []

        # Получаем показатели
        logger.info(" Поиск показателей KPI...")

        indicators = {
            'q1q2': None,
            'q3q4': None,
            'conf': None
        }

        try:
            indicators['q1q2'] = KpiIndicator.objects.get(
                name='Статьи в журналах Scopus/WoS Q1-Q2'
            )
            logger.info(f"✅ Q1-Q2: ID={indicators['q1q2'].id}")
        except KpiIndicator.DoesNotExist:
            logger.warning("⚠️ Q1-Q2 не найден")

        try:
            indicators['q3q4'] = KpiIndicator.objects.get(
                name='Статьи в журналах Scopus/WoS Q3-Q4'
            )
            logger.info(f"✅ Q3-Q4: ID={indicators['q3q4'].id}")
        except KpiIndicator.DoesNotExist:
            logger.warning("⚠️ Q3-Q4 не найден")

        try:
            indicators['conf'] = KpiIndicator.objects.get(
                name='Публикации в трудах конференций'
            )
            logger.info(f"✅ Конференции: ID={indicators['conf'].id}")
        except KpiIndicator.DoesNotExist:
            logger.warning("⚠️ Конференции не найдены")

        if not any(indicators.values()):
            error = "❌ НИ ОДИН показатель не найден! Запустите: python manage.py init_kpi_structure"
            logger.error(error)
            return 0, len(publications), [error]

        logger.info(f" Обрабатываем {len(publications)} публикаций...")

        for idx, pub in enumerate(publications, 1):
            try:
                doi = pub.get('doi', 'NO_DOI')
                pub_type = pub.get('type', '').lower()
                year = pub.get('year')

                logger.info(f"[{idx}/{len(publications)}] {doi} ({pub_type})")

                # Определяем показатель
                indicator = None
                if pub_type == 'journal-article':
                    indicator = indicators['q3q4'] or indicators['q1q2']
                elif pub_type == 'proceedings-article':
                    indicator = indicators['conf']

                if not indicator:
                    logger.info(f"  ⏭️ Пропуск: нет показателя для типа '{pub_type}'")
                    skipped_count += 1
                    continue

                if not year:
                    logger.warning(f"  ⚠️ Пропуск: нет года")
                    skipped_count += 1
                    continue

                period = f"{year}-01"

                # Проверяем дубликат
                existing = KpiValue.objects.filter(
                    user=user,
                    indicator=indicator,
                    period=period,
                    comment__icontains=doi
                ).exists()

                if existing:
                    logger.info(f"  ⏭️ Уже есть")
                    skipped_count += 1
                    continue

                # Сохраняем
                comment = self._format_comment(pub)

                with transaction.atomic():
                    kpi_value, created = KpiValue.objects.get_or_create(
                        user=user,
                        indicator=indicator,
                        period=period,
                        defaults={
                            'actual_value': 1.0,
                            'target_value': indicator.max_value,
                            'comment': comment,
                            'is_verified': True,
                            'status': KpiValue.STATUS_APPROVED
                        }
                    )

                    if not created:
                        kpi_value.actual_value += 1.0
                        kpi_value.comment += f"\n\n{'=' * 50}\n\n{comment}"
                        kpi_value.save()

                    logger.info(f"  ✅ {'Создано' if created else 'Обновлено'} KPI ID={kpi_value.id}")
                    saved_count += 1

            except Exception as e:
                error = f"❌ {pub.get('doi', 'UNKNOWN')}: {str(e)}"
                logger.error(error)
                errors.append(error)

        return saved_count, skipped_count, errors

    def _format_comment(self, pub):
        """Форматирование комментария."""
        authors = ', '.join(pub.get('authors', [])[:3])
        if len(pub.get('authors', [])) > 3:
            authors += ' и др.'

        return f""" {pub['title']}
 {authors}
 {pub.get('journal', 'Не указан')}
 {pub.get('year', 'Не указан')}
 DOI: {pub['doi']}
[Crossref API]"""


class CrossrefSearchByDoiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doi = request.query_params.get('doi')
        if not doi:
            return Response({'error': 'doi required'}, status=400)

        try:
            service = CrossrefAPIService()
            pub = service.get_publication_by_doi(doi)
            return Response(pub if pub else {'error': 'Not found'}, status=200 if pub else 404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class CrossrefSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({'error': 'query required'}, status=400)

        try:
            service = CrossrefAPIService()
            pubs = service.search_publications(query, max_results=20)
            return Response({'publications': pubs, 'count': len(pubs)})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class CrossrefHealthCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            service = CrossrefAPIService()
            service._make_request({'rows': 1})
            return Response({'status': 'ok', 'timestamp': timezone.now().isoformat()})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=503)