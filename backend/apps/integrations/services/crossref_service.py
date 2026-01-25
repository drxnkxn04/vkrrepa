# backend/apps/integrations/services/crossref_service.py

import requests
import logging
import time
from typing import List, Dict, Optional
from django.conf import settings
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError,
    HTTPError
)

logger = logging.getLogger(__name__)


class CrossrefAPIError(Exception):
    """Базовое исключение для ошибок Crossref API"""
    pass


class CrossrefTimeoutError(CrossrefAPIError):
    """Исключение при превышении времени ожидания"""
    pass


class CrossrefConnectionError(CrossrefAPIError):
    """Исключение при проблемах с подключением"""
    pass


class CrossrefRateLimitError(CrossrefAPIError):
    """Исключение при превышении лимита запросов"""
    pass


class CrossrefAPIService:
    """
    Сервис для взаимодействия с Crossref API

    Документация API: https://api.crossref.org/swagger-ui/index.html
    Рекомендации: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
    """

    BASE_URL = "https://api.crossref.org/works"
    REQUEST_DELAY = 1  # Задержка между запросами в секундах

    def __init__(self):
        self.session = requests.Session()

        # Настройка заголовков согласно рекомендациям Crossref
        self.session.headers.update({
            'User-Agent': settings.CROSSREF_USER_AGENT,
            'Accept': 'application/json'
        })

        self.last_request_time = 0
        self.timeout = settings.CROSSREF_TIMEOUT
        self.max_retries = settings.CROSSREF_MAX_RETRIES
        self.retry_delay = settings.CROSSREF_RETRY_DELAY

        logger.info(f"Crossref API инициализирован с User-Agent: {settings.CROSSREF_USER_AGENT}")

    def _wait_for_rate_limit(self):
        """
        Соблюдение рейт-лимита между запросами
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - elapsed
            logger.debug(f"Rate limit: ожидание {sleep_time:.2f}с")
            time.sleep(sleep_time)

    def _make_request(
            self,
            params: Dict,
            endpoint: Optional[str] = None,
            retry_count: int = 0
    ) -> Dict:
        """
        Выполнение запроса к Crossref API с обработкой ошибок и повторными попытками

        Args:
            params: Параметры запроса
            endpoint: Дополнительный путь к эндпоинту (если не BASE_URL)
            retry_count: Текущая попытка (для рекурсии)

        Returns:
            Dict с данными ответа

        Raises:
            CrossrefTimeoutError: При превышении времени ожидания
            CrossrefConnectionError: При проблемах с подключением
            CrossrefRateLimitError: При превышении лимита запросов
            CrossrefAPIError: При других ошибках API
        """
        self._wait_for_rate_limit()

        # Добавляем mailto для получения приоритета в очереди запросов
        params['mailto'] = settings.CROSSREF_MAILTO

        url = endpoint if endpoint else self.BASE_URL

        try:
            logger.debug(f"Запрос к Crossref API: {url} с параметрами {params}")

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )

            self.last_request_time = time.time()

            # Проверка статус-кода
            if response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                logger.warning(f"Rate limit превышен. Повтор через {retry_after}с")

                if retry_count < self.max_retries:
                    time.sleep(retry_after)
                    return self._make_request(params, endpoint, retry_count + 1)
                else:
                    raise CrossrefRateLimitError(
                        f"Превышен лимит попыток после {self.max_retries} повторов"
                    )

            response.raise_for_status()

            data = response.json()
            logger.info(f"Успешный запрос к Crossref API. Статус: {data.get('status')}")

            return data

        except Timeout as e:
            logger.error(f"Таймаут при запросе к Crossref API: {str(e)}")

            if retry_count < self.max_retries:
                logger.info(f"Повторная попытка {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)
                return self._make_request(params, endpoint, retry_count + 1)
            else:
                raise CrossrefTimeoutError(
                    f"Превышено время ожидания после {self.max_retries} попыток"
                ) from e

        except ConnectionError as e:
            logger.error(f"Ошибка подключения к Crossref API: {str(e)}")

            if retry_count < self.max_retries:
                logger.info(f"Повторная попытка {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay * 2)  # Увеличенная задержка при проблемах с сетью
                return self._make_request(params, endpoint, retry_count + 1)
            else:
                raise CrossrefConnectionError(
                    f"Не удалось подключиться после {self.max_retries} попыток"
                ) from e

        except HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None
            logger.error(f"HTTP ошибка от Crossref API. Статус: {status_code}, Текст: {e}")

            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Тело ответа: {e.response.text}")

            raise CrossrefAPIError(
                f"Ошибка HTTP {status_code}: {str(e)}"
            ) from e

        except RequestException as e:
            logger.error(f"Общая ошибка при запросе к Crossref API: {str(e)}")
            raise CrossrefAPIError(f"Ошибка запроса: {str(e)}") from e

    def get_publications_by_orcid(
            self,
            orcid: str,
            year: Optional[int] = None,
            max_results: int = 100
    ) -> List[Dict]:
        """
        Получение публикаций автора по ORCID

        Args:
            orcid: ORCID идентификатор (формат: 0000-0000-0000-0000)
            year: Фильтр по году публикации (опционально)
            max_results: Максимальное количество результатов

        Returns:
            List словарей с данными публикаций

        Raises:
            ValueError: При неверном формате ORCID
            CrossrefAPIError: При ошибках API
        """
        # Валидация формата ORCID
        if not self._validate_orcid(orcid):
            raise ValueError(
                f"Неверный формат ORCID: {orcid}. "
                f"Ожидается формат: 0000-0000-0000-0000"
            )

        params = {
            'filter': f'orcid:{orcid}',
            'select': 'DOI,title,published,container-title,type,author,abstract,publisher',
            'rows': min(max_results, 1000),  # Crossref ограничивает до 1000
        }

        if year:
            params['filter'] += f',from-pub-date:{year}-01-01,until-pub-date:{year}-12-31'

        try:
            data = self._make_request(params)
            items = data.get('message', {}).get('items', [])

            logger.info(f"Найдено {len(items)} публикаций для ORCID {orcid}")

            return self._process_works(items)

        except CrossrefAPIError as e:
            logger.error(f"Ошибка получения публикаций для ORCID {orcid}: {str(e)}")
            raise

    def get_publication_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Получение данных публикации по DOI

        Args:
            doi: Digital Object Identifier

        Returns:
            Dict с данными публикации или None при ошибке
        """
        if not doi:
            logger.warning("Пустой DOI передан в get_publication_by_doi")
            return None

        # Очистка DOI от лишних символов
        clean_doi = doi.strip().replace('https://doi.org/', '').replace('http://dx.doi.org/', '')

        endpoint = f"https://api.crossref.org/works/{clean_doi}"

        try:
            data = self._make_request({}, endpoint)
            work = data.get('message', {})

            if work:
                processed = self._process_works([work])
                return processed[0] if processed else None

            return None

        except CrossrefAPIError as e:
            logger.error(f"Ошибка получения публикации по DOI {doi}: {str(e)}")
            return None

    def search_publications(
            self,
            query: str,
            max_results: int = 20
    ) -> List[Dict]:
        """
        Поиск публикаций по запросу

        Args:
            query: Поисковый запрос (название, автор, etc.)
            max_results: Максимальное количество результатов

        Returns:
            List найденных публикаций
        """
        params = {
            'query': query,
            'rows': min(max_results, 100),
            'select': 'DOI,title,published,container-title,type,author'
        }

        try:
            data = self._make_request(params)
            items = data.get('message', {}).get('items', [])

            logger.info(f"Найдено {len(items)} публикаций по запросу '{query}'")

            return self._process_works(items)

        except CrossrefAPIError as e:
            logger.error(f"Ошибка поиска публикаций по запросу '{query}': {str(e)}")
            return []

    def _process_works(self, works: List[Dict]) -> List[Dict]:
        """
        Обработка и нормализация полученных данных о публикациях

        Args:
            works: Список raw данных от Crossref

        Returns:
            List обработанных публикаций
        """
        processed_works = []

        for work in works:
            try:
                # Пропускаем публикации без базовых данных
                if not work.get('title') or not work.get('DOI'):
                    logger.debug(f"Пропуск публикации без title или DOI")
                    continue

                # Фильтрация по типу публикации
                publication_type = work.get('type', '').lower()
                if not self._is_valid_publication_type(publication_type):
                    logger.debug(f"Пропуск публикации типа: {publication_type}")
                    continue

                # Извлечение года публикации
                published_date = work.get('published', {}).get('date-parts', [[None]])[0]
                publication_year = published_date[0] if published_date and published_date[0] else None

                # Обработка авторов
                authors = self._extract_authors(work.get('author', []))

                # Обработка названия (может быть списком)
                title = work['title'][0] if isinstance(work['title'], list) and work['title'] else work['title']

                # Обработка журнала
                journal = work.get('container-title', [''])[0] if isinstance(
                    work.get('container-title'), list
                ) else work.get('container-title', '')

                # Формирование структуры публикации
                publication = {
                    'doi': work['DOI'].upper(),
                    'title': str(title).strip(),
                    'year': publication_year,
                    'journal': str(journal).strip(),
                    'publisher': work.get('publisher', ''),
                    'type': publication_type,
                    'authors': authors,
                    'abstract': work.get('abstract', '').replace('\n', ' ').strip()[:500],  # Ограничиваем
                    'url': f"https://doi.org/{work['DOI']}"
                }

                processed_works.append(publication)

            except Exception as e:
                logger.error(f"Ошибка обработки публикации {work.get('DOI', 'UNKNOWN')}: {str(e)}")
                continue

        logger.info(f"Обработано {len(processed_works)} из {len(works)} публикаций")
        return processed_works

    def _extract_authors(self, authors_data: List[Dict]) -> List[str]:
        """Извлечение и форматирование списка авторов"""
        authors = []

        for author in authors_data:
            given_name = author.get('given', '').strip()
            family_name = author.get('family', '').strip()

            if given_name and family_name:
                authors.append(f"{given_name} {family_name}")
            elif family_name:
                authors.append(family_name)

        return authors

    def _is_valid_publication_type(self, pub_type: str) -> bool:
        """
        Проверка, является ли тип публикации релевантным

        Согласно документу ВКР, учитываются:
        - Статьи в журналах
        - Статьи в трудах конференций
        - Препринты
        """
        valid_types = {
            'journal-article',
            'proceedings-article',
            'posted-content',
            'book-chapter'
        }

        return pub_type in valid_types

    def _validate_orcid(self, orcid: str) -> bool:
        """
        Валидация формата ORCID

        Формат: 0000-0000-0000-0000 (4 группы по 4 цифры через дефис)
        """
        import re
        pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
        return bool(re.match(pattern, orcid))