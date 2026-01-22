import requests
import logging
import json
import time
from django.conf import settings
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class CrossrefAPIService:
    """
    Сервис для взаимодействия с Crossref API
    """
    BASE_URL = "https://api.crossref.org/works"
    REQUEST_DELAY = 1  # Задержка между запросами в секундах

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': settings.CROSSREF_USER_AGENT,
            'Accept': 'application/json'
        })
        self.last_request_time = 0

    def _make_request(self, params, timeout=30):
        """Выполнение запроса с соблюдением рейт-лимита"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)

        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            self.last_request_time = time.time()
            return response.json()
        except RequestException as e:
            logger.error(f"Ошибка при запросе к Crossref API: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Статус код: {e.response.status_code}")
                logger.error(f"Тело ответа: {e.response.text}")
            raise

    def get_publications_by_orcid(self, orcid, year=None):
        """Получение публикаций автора по ORCID"""
        params = {
            'filter': f'orcid:{orcid}',
            'select': 'DOI,title,published,container-title,type,author,abstract',
            'rows': 100,
            'mailto': settings.CROSSREF_MAILTO
        }

        if year:
            params['filter'] += f',from-pub-date:{year}-01-01,until-pub-date:{year}-12-31'

        data = self._make_request(params)
        return self._process_works(data.get('message', {}).get('items', []))

    def _process_works(self, works):
        """Обработка полученных данных о публикациях"""
        processed_works = []

        for work in works:
            # Пропускаем публикации без названия или DOI
            if not work.get('title') or not work.get('DOI'):
                continue

            # Пропускаем нерелевантные типы публикаций
            publication_type = work.get('type', '').lower()
            if publication_type not in ['journal-article', 'proceedings-article', 'posted-content']:
                continue

            # Извлечение года публикации
            published_date = work.get('published', {}).get('date-parts', [[None]])[0]
            publication_year = published_date[0] if published_date and published_date[0] else None

            # Обработка авторов
            authors = []
            for author in work.get('author', []):
                given_name = author.get('given', '').strip()
                family_name = author.get('family', '').strip()

                if given_name and family_name:
                    authors.append(f"{given_name} {family_name}")

            # Формирование структуры публикации
            publication = {
                'doi': work['DOI'].upper(),
                'title': work['title'][0] if isinstance(work['title'], list) and work['title'] else work['title'],
                'year': publication_year,
                'journal': work.get('container-title', [''])[0] if isinstance(work.get('container-title'),
                                                                              list) else work.get('container-title',
                                                                                                  ''),
                'type': publication_type,
                'authors': authors,
                'abstract': work.get('abstract', '').replace('\n', ' ').strip(),
                'url': f"https://doi.org/{work['DOI']}"
            }

            processed_works.append(publication)

        return processed_works