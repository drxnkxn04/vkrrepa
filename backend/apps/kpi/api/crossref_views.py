# backend/apps/kpi/api/crossref_views.py

from collections import defaultdict
import logging
import re

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.services.crossref_service import (
    CrossrefAPIError,
    CrossrefAPIService,
    CrossrefConnectionError,
    CrossrefRateLimitError,
    CrossrefTimeoutError,
    CrossrefValidationError,
)
from apps.kpi.models import KpiIndicator, KpiValue

logger = logging.getLogger(__name__)


class CrossrefSyncView(APIView):
    """
    Sync Crossref publications and store them in KPI.

    Storage strategy:
    - one KpiValue per (user, indicator, period)
    - actual_value = number of unique DOIs
    """

    permission_classes = [IsAuthenticated]

    DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)

    def post(self, request, *args, **kwargs):
        user = request.user
        orcid = request.data.get('orcid')
        year = request.data.get('year')
        save_to_kpi = request.data.get('save_to_kpi', False)
        selected_dois = request.data.get('selected_dois')

        if not orcid and hasattr(user, 'profile') and user.profile.orcid:
            orcid = user.profile.orcid

        if not orcid:
            return Response(
                {'success': False, 'error': 'ORCID is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            normalized_year = self._normalize_year(year)
            crossref_service = CrossrefAPIService()

            publications = crossref_service.get_publications_by_orcid(
                orcid=orcid,
                year=normalized_year,
                max_results=100,
            )

            saved_count = 0
            skipped_count = 0
            errors = []

            if save_to_kpi and publications:
                pubs_to_save = publications
                if selected_dois:
                    doi_set = {d.strip().upper() for d in selected_dois}
                    pubs_to_save = [
                        p for p in publications
                        if (p.get('doi') or '').strip().upper() in doi_set
                    ]
                saved_count, skipped_count, errors = self._save_publications_to_kpi(
                    user=user,
                    publications=pubs_to_save,
                )

            return Response(
                {
                    'success': True,
                    'publications_count': len(publications),
                    'saved_to_kpi': saved_count,
                    'skipped': skipped_count,
                    'errors': errors,
                    'publications': publications,
                    'orcid': orcid,
                    'year': normalized_year,
                }
            )

        except ValueError as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CrossrefValidationError as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CrossrefRateLimitError as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except (CrossrefTimeoutError, CrossrefConnectionError) as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except CrossrefAPIError as exc:
            return Response(
                {'success': False, 'error': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as exc:
            logger.exception('Unexpected error in Crossref sync: %s', exc)
            return Response(
                {'success': False, 'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _normalize_year(self, year):
        if year in (None, '', 'null'):
            return None

        try:
            year_int = int(year)
        except (TypeError, ValueError) as exc:
            raise ValueError('year must be an integer') from exc

        current_year = timezone.now().year
        if year_int < 1900 or year_int > current_year + 1:
            raise ValueError(f'year is out of range: 1900..{current_year + 1}')

        return year_int

    def _save_publications_to_kpi(self, user, publications):
        saved_count = 0
        skipped_count = 0
        errors = []

        indicators = self._get_indicators(user=user)
        if not any(indicators.values()):
            error = 'Publication KPI indicators are missing. Run init_kpi_structure.'
            logger.error(error)
            return 0, len(publications), [error]

        grouped = defaultdict(list)

        for pub in publications:
            doi = (pub.get('doi') or '').strip().upper()
            pub_type = (pub.get('type') or '').strip().lower()
            year = pub.get('year')

            if not doi or not year:
                skipped_count += 1
                continue

            indicator = self._select_indicator(pub_type, indicators)
            if indicator is None:
                skipped_count += 1
                continue

            period = f'{int(year)}-01'
            grouped[(indicator.id, period)].append(pub)

        indicator_map = {indicator.id: indicator for indicator in indicators.values() if indicator}

        for (indicator_id, period), group_pubs in grouped.items():
            indicator = indicator_map.get(indicator_id)
            if indicator is None:
                skipped_count += len(group_pubs)
                continue

            unique_in_batch = {}
            for pub in group_pubs:
                doi = pub['doi'].strip().upper()
                unique_in_batch[doi] = pub

            try:
                with transaction.atomic():
                    kpi_value, _ = KpiValue.objects.get_or_create(
                        user=user,
                        indicator=indicator,
                        period=period,
                        defaults={
                            'actual_value': 0.0,
                            'target_value': indicator.max_value,
                            'is_verified': True,
                            'status': KpiValue.STATUS_APPROVED,
                            'comment': '',
                        },
                    )

                    existing_dois = self._extract_dois_from_comment(kpi_value.comment)
                    new_pubs = [
                        pub for doi, pub in unique_in_batch.items() if doi not in existing_dois
                    ]

                    if not new_pubs:
                        skipped_count += len(unique_in_batch)
                        continue

                    merged_dois = existing_dois | set(unique_in_batch.keys())
                    kpi_value.actual_value = float(len(merged_dois))
                    kpi_value.target_value = indicator.max_value
                    kpi_value.is_verified = True
                    kpi_value.status = KpiValue.STATUS_APPROVED
                    kpi_value.comment = self._append_sync_block(kpi_value.comment, new_pubs)
                    kpi_value.save(
                        update_fields=[
                            'actual_value',
                            'target_value',
                            'is_verified',
                            'status',
                            'comment',
                            'updated_at',
                        ]
                    )

                    saved_count += len(new_pubs)
                    skipped_count += len(unique_in_batch) - len(new_pubs)

            except Exception as exc:
                err = f'KPI save error (indicator={indicator_id}, period={period}): {exc}'
                logger.error(err)
                errors.append(err)

        logger.info(
            'Crossref sync summary: saved=%s skipped=%s errors=%s',
            saved_count,
            skipped_count,
            len(errors),
        )
        return saved_count, skipped_count, errors

    def _get_indicators(self, user=None):
        """Поиск показателей для публикаций с фильтрацией по роли."""
        indicators = {'journal': None, 'conf': None}

        # Базовый queryset с фильтром по роли
        base_qs = KpiIndicator.objects.filter(data_source='api')
        if user:
            profile = getattr(user, 'profile', None)
            user_role = profile.role if profile and profile.role else ('rop' if user.is_staff else 'pps')
            base_qs = base_qs.filter(group__role=user_role)

        # Журнальные публикации
        indicators['journal'] = (
            base_qs.filter(name__icontains='журнал').first()
            or base_qs.filter(name__icontains='публикаци').first()
            or base_qs.filter(name__icontains='Q1-Q2').first()
            or base_qs.filter(name__icontains='Q3-Q4').first()
        )
        if indicators['journal'] is None:
            logger.warning('Indicator not found: journal publications')

        # Конференции
        indicators['conf'] = (
            base_qs.filter(name__icontains='CORE').first()
            or base_qs.filter(name__icontains='\u043a\u043e\u043d\u0444\u0435\u0440\u0435\u043d\u0446').first()
            or base_qs.filter(name__icontains='conference').first()
        )
        if indicators['conf'] is None:
            logger.warning('Indicator not found: conferences')

        return indicators

    def _select_indicator(self, pub_type, indicators):
        if pub_type == 'journal-article':
            return indicators['journal']
        if pub_type == 'proceedings-article':
            return indicators['conf']
        return None

    def _extract_dois_from_comment(self, comment):
        if not comment:
            return set()
        return {match.group(0).upper() for match in self.DOI_PATTERN.finditer(comment)}

    def _append_sync_block(self, existing_comment, publications):
        ts = timezone.now().strftime('%Y-%m-%d %H:%M')
        lines = [f'=== Crossref sync {ts} ===']

        for pub in publications:
            lines.append(self._format_publication_line(pub))

        block = '\n'.join(lines)
        if existing_comment and existing_comment.strip():
            return f'{existing_comment.strip()}\n\n{block}'
        return block

    def _format_publication_line(self, pub):
        title = (pub.get('title') or '').strip()
        year = pub.get('year') or 'N/A'
        doi = (pub.get('doi') or '').strip().upper()
        journal = (pub.get('journal') or '').strip()
        return f'- {year} | {title} | {journal} | DOI: {doi}'


class CrossrefSearchByDoiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        doi = request.query_params.get('doi')
        if not doi:
            return Response({'error': 'doi required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = CrossrefAPIService()
            publication = service.get_publication_by_doi(doi)
            if publication is None:
                return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response(publication)
        except CrossrefValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except CrossrefRateLimitError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (CrossrefTimeoutError, CrossrefConnectionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except CrossrefAPIError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            logger.exception('Unexpected DOI search error: %s', exc)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrossrefSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({'error': 'query required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = CrossrefAPIService()
            publications = service.search_publications(query, max_results=20)
            return Response({'publications': publications, 'count': len(publications)})
        except CrossrefValidationError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except CrossrefRateLimitError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except (CrossrefTimeoutError, CrossrefConnectionError) as exc:
            return Response({'error': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except CrossrefAPIError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            logger.exception('Unexpected Crossref search error: %s', exc)
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrossrefSaveToKpiView(APIView):
    """
    Save publications (from DOI/search) to KPI.

    POST /api/kpi/crossref/save-to-kpi/
    Body: { publications: [{doi, title, year, journal, type, authors, url}, ...] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        publications = request.data.get('publications', [])
        if not publications:
            return Response(
                {'success': False, 'error': 'No publications provided'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sync_view = CrossrefSyncView()
        saved_count, skipped_count, errors = sync_view._save_publications_to_kpi(
            user=request.user,
            publications=publications,
        )

        return Response({
            'success': True,
            'saved_to_kpi': saved_count,
            'skipped': skipped_count,
            'errors': errors,
        })


class CrossrefHealthCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = CrossrefAPIService()
        result = service.health_check()

        payload = {
            'status': result.get('status', 'error'),
            'timestamp': timezone.now().isoformat(),
        }
        if result.get('status') != 'ok':
            payload['message'] = result.get('message', 'Crossref unavailable')
            return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(payload)
