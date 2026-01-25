# backend/apps/kpi/api/crossref_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging
from apps.integrations.services.crossref_service import (
    CrossrefAPIService,
    CrossrefAPIError,
    CrossrefTimeoutError,
    CrossrefConnectionError,
    CrossrefRateLimitError
)
logger = logging.getLogger(__name__)


class CrossrefSyncView(APIView):
    """
    Синхронизация публикаций из Crossref API по ORCID.

    POST /api/kpi/crossref/sync/

    Body:
    {
        "orcid": "0000-0000-0000-0000",
        "year": 2024  // опционально
    }

    Returns:
    {
        "success": true,
        "publications_count": 10,
        "publications": [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        orcid = request.data.get('orcid')
        year = request.data.get('year')

        # Валидация входных данных
        if not orcid:
            if hasattr(user, 'profile') and user.profile.orcid:
                orcid = user.profile.orcid
            else:
                return Response(
                    {
                        'success': False,
                        'error': 'ORCID не указан. Добавьте ORCID в профиль или передайте в запросе.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            # Инициализируем сервис Crossref
            crossref_service = CrossrefAPIService()

            logger.info(f"Начало синхронизации публикаций для пользователя {user.username} с ORCID {orcid}")

            # Получаем публикации
            publications = crossref_service.get_publications_by_orcid(
                orcid=orcid,
                year=year,
                max_results=100
            )

            logger.info(f"Найдено {len(publications)} публикаций для ORCID {orcid}")

            return Response({
                'success': True,
                'publications_count': len(publications),
                'publications': publications,
                'orcid': orcid,
                'year': year
            })

        except ValueError as e:
            # Неверный формат ORCID
            logger.warning(f"Неверный формат ORCID {orcid}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Неверный формат ORCID: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except CrossrefTimeoutError as e:
            logger.error(f"Таймаут при запросе к Crossref для {orcid}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Превышено время ожидания. Попробуйте уменьшить диапазон поиска.'
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except CrossrefRateLimitError as e:
            logger.error(f"Превышен лимит запросов к Crossref: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Превышен лимит запросов. Пожалуйста, попробуйте через несколько минут.'
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        except CrossrefConnectionError as e:
            logger.error(f"Ошибка подключения к Crossref: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Не удалось подключиться к Crossref API. Проверьте интернет-соединение.'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except CrossrefAPIError as e:
            logger.error(f"Ошибка Crossref API для {orcid}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Ошибка API Crossref: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при синхронизации для {orcid}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': 'Произошла непредвиденная ошибка. Попробуйте позже.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossrefSearchByDoiView(APIView):
    """
    Поиск публикации по DOI.

    GET /api/kpi/crossref/search-by-doi/?doi=10.1000/xyz123

    Returns:
    {
        "doi": "10.1000/XYZ123",
        "title": "...",
        "year": 2024,
        ...
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        doi = request.query_params.get('doi')

        if not doi:
            return Response(
                {'error': 'Параметр doi обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            crossref_service = CrossrefAPIService()

            logger.info(f"Поиск публикации по DOI: {doi}")

            publication = crossref_service.get_publication_by_doi(doi)

            if publication:
                logger.info(f"Публикация найдена: {publication['title']}")
                return Response(publication)
            else:
                logger.warning(f"Публикация с DOI {doi} не найдена")
                return Response(
                    {'error': 'Публикация не найдена'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except CrossrefTimeoutError as e:
            logger.error(f"Таймаут при поиске DOI {doi}: {str(e)}")
            return Response(
                {'error': 'Превышено время ожидания'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except CrossrefAPIError as e:
            logger.error(f"Ошибка API при поиске DOI {doi}: {str(e)}")
            return Response(
                {'error': f'Ошибка поиска: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при поиске DOI {doi}: {str(e)}")
            return Response(
                {'error': 'Произошла ошибка при поиске'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossrefSearchView(APIView):
    """
    Поиск публикаций по текстовому запросу.

    GET /api/kpi/crossref/search/?query=machine+learning&max_results=20

    Returns:
    {
        "publications": [...],
        "count": 20,
        "query": "machine learning"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query')
        max_results = int(request.query_params.get('max_results', 20))

        if not query:
            return Response(
                {'error': 'Параметр query обязателен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ограничение на количество результатов
        if max_results > 100:
            max_results = 100

        try:
            crossref_service = CrossrefAPIService()

            logger.info(f"Поиск публикаций по запросу: '{query}', лимит: {max_results}")

            publications = crossref_service.search_publications(
                query=query,
                max_results=max_results
            )

            logger.info(f"Найдено {len(publications)} публикаций по запросу '{query}'")

            return Response({
                'publications': publications,
                'count': len(publications),
                'query': query
            })

        except CrossrefTimeoutError as e:
            logger.error(f"Таймаут при поиске '{query}': {str(e)}")
            return Response(
                {'error': 'Превышено время ожидания'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )

        except CrossrefRateLimitError as e:
            logger.error(f"Превышен лимит запросов при поиске '{query}': {str(e)}")
            return Response(
                {'error': 'Превышен лимит запросов. Попробуйте позже.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        except CrossrefAPIError as e:
            logger.error(f"Ошибка API при поиске '{query}': {str(e)}")
            return Response(
                {'error': f'Ошибка поиска: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.exception(f"Непредвиденная ошибка при поиске '{query}': {str(e)}")
            return Response(
                {'error': 'Произошла ошибка при поиске'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CrossrefHealthCheckView(APIView):
    """
    Проверка доступности Crossref API.

    GET /api/kpi/crossref/health/

    Returns:
    {
        "status": "ok",
        "timestamp": "2024-01-24T12:00:00Z"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            crossref_service = CrossrefAPIService()

            # Пробуем выполнить простой запрос
            test_doi = "10.1000/xyz"  # Несуществующий DOI для теста
            crossref_service._make_request({'rows': 1})

            return Response({
                'status': 'ok',
                'message': 'Crossref API доступен',
                'timestamp': timezone.now().isoformat()
            })

        except CrossrefConnectionError:
            return Response(
                {
                    'status': 'error',
                    'message': 'Не удалось подключиться к Crossref API',
                    'timestamp': timezone.now().isoformat()
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Ошибка проверки: {str(e)}',
                    'timestamp': timezone.now().isoformat()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )