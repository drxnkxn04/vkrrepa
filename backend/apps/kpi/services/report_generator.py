# backend/apps/kpi/report_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime
import os
import logging

from .kpi_calculator import KpiCalculator

User = get_user_model()
logger = logging.getLogger(__name__)


class KpiReportGenerator:
    """
    Генератор PDF-отчетов по KPI для сотрудников.
    """

    def __init__(self):
        self.calculator = KpiCalculator()
        self.styles = getSampleStyleSheet()

        # Регистрация русского шрифта (если доступен)
        try:
            # Попытка использовать DejaVu для поддержки кириллицы
            font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('DejaVu', font_path))
                self.font_name = 'DejaVu'
            else:
                self.font_name = 'Helvetica'
        except Exception as e:
            logger.warning(f"Не удалось загрузить русский шрифт: {e}")
            self.font_name = 'Helvetica'

        # Создание пользовательских стилей
        self._setup_styles()

    def _setup_styles(self):
        """Настройка стилей для документа."""

        # Заголовок
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=1  # Центрирование
        ))

        # Подзаголовок
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontName=self.font_name,
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        ))

        # Обычный текст
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=6
        ))

    def generate_user_report(self, user_id: int, period: str) -> str:
        """
        Генерация PDF-отчета для конкретного пользователя.

        Args:
            user_id: ID пользователя
            period: Период в формате 'YYYY-MM'

        Returns:
            Путь к сгенерированному файлу
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Пользователь с ID {user_id} не найден")
            raise

        # Получаем данные для отчета
        kpi_data = self.calculator.calculate_dashboard(user_id, period)
        recommendations = self.calculator.generate_recommendations(user_id, period)
        history = self.calculator.get_user_kpi_history(user_id, months=6)

        # Создание пути для сохранения файла
        report_dir = os.path.join(settings.MEDIA_ROOT, 'reports', str(user_id))
        os.makedirs(report_dir, exist_ok=True)

        filename = f"KPI_Report_{user.username}_{period}.pdf"
        filepath = os.path.join(report_dir, filename)

        # Создание PDF
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        # Построение содержимого отчета
        story = []

        # Титульный лист
        story.extend(self._build_title_page(user, period, kpi_data))

        # Общая информация
        story.extend(self._build_summary_section(kpi_data))

        # Детальная информация по группам
        story.extend(self._build_groups_section(kpi_data))

        # История KPI
        story.extend(self._build_history_section(history))

        # Рекомендации
        if recommendations:
            story.extend(self._build_recommendations_section(recommendations))

        # Сборка документа
        doc.build(story)

        logger.info(f"Отчет сгенерирован: {filepath}")

        return filepath

    def _build_title_page(self, user: User, period: str, kpi_data: dict) -> list:
        """Построение титульного листа."""
        elements = []

        # Заголовок
        title = Paragraph(
            "ОТЧЕТ ПО КЛЮЧЕВЫМ ПОКАЗАТЕЛЯМ ЭФФЕКТИВНОСТИ",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 1 * cm))

        # Информация о сотруднике
        user_info = f"""
        <b>Сотрудник:</b> {user.get_full_name() or user.username}<br/>
        <b>Период:</b> {self._format_period(period)}<br/>
        <b>Дата формирования отчета:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        elements.append(Paragraph(user_info, self.styles['CustomBody']))
        elements.append(Spacer(1, 2 * cm))

        # Общий балл (крупно)
        score = kpi_data['total_score']
        level = kpi_data['performance_level']

        score_text = f"""
        <para align=center>
        <font size=48 color="{self._get_score_color(score)}"><b>{score:.1f}</b></font><br/>
        <font size=14>Итоговый балл KPI</font><br/>
        <font size=12 color="{self._get_level_color(level)}">
        <b>{self._format_level(level)}</b>
        </font>
        </para>
        """
        elements.append(Paragraph(score_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 1 * cm))

        # Премия
        bonus = kpi_data['bonus_amount']
        bonus_text = f"""
        <para align=center>
        <font size=16><b>Премия: {bonus:,.0f} ₽</b></font>
        </para>
        """
        elements.append(Paragraph(bonus_text, self.styles['CustomBody']))

        elements.append(PageBreak())

        return elements

    def _build_summary_section(self, kpi_data: dict) -> list:
        """Построение секции общей информации."""
        elements = []

        heading = Paragraph("1. ОБЩАЯ ИНФОРМАЦИЯ", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.5 * cm))

        # Таблица с основными показателями
        data = [
            ['Показатель', 'Значение'],
            ['Итоговый балл KPI', f"{kpi_data['total_score']:.1f}%"],
            ['Уровень эффективности', self._format_level(kpi_data['performance_level'])],
            ['Премиальная выплата', f"{kpi_data['bonus_amount']:,.0f} ₽"],
        ]

        table = Table(data, colWidths=[10 * cm, 6 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 1 * cm))

        return elements

    def _build_groups_section(self, kpi_data: dict) -> list:
        """Построение секции с детализацией по группам."""
        elements = []

        heading = Paragraph("2. ДЕТАЛИЗАЦИЯ ПО ГРУППАМ ПОКАЗАТЕЛЕЙ", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.5 * cm))

        for group_id, group_data in kpi_data['group_scores'].items():
            # Название группы
            group_title = Paragraph(
                f"<b>{group_data['name']}</b> - {group_data['score']:.1f}%",
                self.styles['CustomBody']
            )
            elements.append(group_title)
            elements.append(Spacer(1, 0.3 * cm))

            # Таблица с показателями группы
            table_data = [['Показатель', 'Факт', 'План', 'Выполнение']]

            for indicator in group_data['indicators']:
                table_data.append([
                    indicator['name'],
                    f"{indicator['actual_value']:.1f} {indicator['unit']}",
                    f"{indicator['target_value']:.1f} {indicator['unit']}",
                    f"{indicator['completion_percent']:.1f}%"
                ])

            table = Table(table_data, colWidths=[7 * cm, 3 * cm, 3 * cm, 3 * cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.8 * cm))

        return elements

    def _build_history_section(self, history: list) -> list:
        """Построение секции с историей KPI."""
        elements = []

        heading = Paragraph("3. ДИНАМИКА KPI ЗА ПОСЛЕДНИЕ 6 МЕСЯЦЕВ", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.5 * cm))

        # Таблица с историей
        table_data = [['Период', 'Балл KPI', 'Уровень', 'Премия']]

        for item in history:
            table_data.append([
                self._format_period(item['period']),
                f"{item['total_score']:.1f}%",
                self._format_level(item['performance_level']),
                f"{item['bonus_amount']:,.0f} ₽"
            ])

        table = Table(table_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ECC71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        elements.append(table)
        elements.append(Spacer(1, 1 * cm))

        return elements

    def _build_recommendations_section(self, recommendations: list) -> list:
        """Построение секции с рекомендациями."""
        elements = []

        heading = Paragraph("4. РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ ПОКАЗАТЕЛЕЙ", self.styles['CustomHeading'])
        elements.append(heading)
        elements.append(Spacer(1, 0.5 * cm))

        for i, rec in enumerate(recommendations, 1):
            rec_text = f"""
            <b>{i}. {rec['indicator_name']}</b><br/>
            <i>Текущее выполнение: {rec['current_completion']:.1f}%</i><br/>
            {rec['text']}<br/>
            <b>Целевое значение:</b> {rec['target_value']:.1f}<br/>
            <b>Срок:</b> {self._format_period(rec['deadline_period'])}
            """
            elements.append(Paragraph(rec_text, self.styles['CustomBody']))
            elements.append(Spacer(1, 0.5 * cm))

        return elements

    def _format_period(self, period: str) -> str:
        """Форматирование периода для отображения."""
        months = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
            '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
            '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
        }
        year, month = period.split('-')
        return f"{months[month]} {year}"

    def _format_level(self, level: str) -> str:
        """Форматирование уровня эффективности."""
        levels = {
            'высокий': 'Высокая эффективность',
            'средний': 'Средняя эффективность',
            'низкий': 'Низкая эффективность'
        }
        return levels.get(level, level)

    def _get_score_color(self, score: float) -> str:
        """Определение цвета для балла."""
        if score >= 90:
            return '#27AE60'  # Зеленый
        elif score >= 70:
            return '#F39C12'  # Оранжевый
        else:
            return '#E74C3C'  # Красный

    def _get_level_color(self, level: str) -> str:
        """Определение цвета для уровня эффективности."""
        colors_map = {
            'высокий': '#27AE60',
            'средний': '#F39C12',
            'низкий': '#E74C3C'
        }
        return colors_map.get(level, '#95A5A6')

    def generate_report_response(self, user_id: int, period: str):
        """
        Генерация PDF-отчета для HTTP-ответа (без сохранения на диск).

        Args:
            user_id: ID пользователя
            period: Период в формате 'YYYY-MM'

        Returns:
            BytesIO объект с PDF
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise

        # Получаем данные
        kpi_data = self.calculator.calculate_dashboard(user_id, period)
        recommendations = self.calculator.generate_recommendations(user_id, period)
        history = self.calculator.get_user_kpi_history(user_id, months=6)

        # Создаем PDF в памяти
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Построение содержимого
        story = []
        story.extend(self._build_title_page(user, period, kpi_data))
        story.extend(self._build_summary_section(kpi_data))
        story.extend(self._build_groups_section(kpi_data))
        story.extend(self._build_history_section(history))

        if recommendations:
            story.extend(self._build_recommendations_section(recommendations))

        # Сборка
        doc.build(story)

        buffer.seek(0)
        return buffer