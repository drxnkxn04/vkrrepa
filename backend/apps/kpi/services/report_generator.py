# backend/apps/kpi/services/report_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime
import os
import logging

from .kpi_calculator import KpiCalculator

User = get_user_model()
logger = logging.getLogger(__name__)

BLUE      = colors.HexColor('#1a73e8')
DARK      = colors.HexColor('#1e2a38')
GRAY_BG   = colors.HexColor('#f5f7fa')
GRAY_LINE = colors.HexColor('#dee2e6')
GREEN     = colors.HexColor('#28a745')
YELLOW    = colors.HexColor('#ffc107')
RED       = colors.HexColor('#dc3545')
WHITE     = colors.white


def _score_color(score: float):
    if score >= 90: return GREEN
    if score >= 70: return YELLOW
    return RED


def _load_fonts(base_dir):
    """Регистрирует Arial с кириллицей, возвращает (regular, bold)."""
    font_dir = os.path.join(base_dir, 'fonts')
    reg  = os.path.join(font_dir, 'Arial.ttf')
    bold = os.path.join(font_dir, 'Arial-Bold.ttf')
    if os.path.exists(reg) and os.path.exists(bold):
        try:
            pdfmetrics.registerFont(TTFont('Arial', reg))
            pdfmetrics.registerFont(TTFont('Arial-Bold', bold))
            return 'Arial', 'Arial-Bold'
        except Exception as e:
            logger.warning(f'Не удалось загрузить Arial: {e}')
    return 'Helvetica', 'Helvetica-Bold'


class KpiReportGenerator:
    """Генератор PDF и Excel отчётов по KPI."""

    def __init__(self):
        self.calculator = KpiCalculator()
        self.font, self.font_bold = _load_fonts(settings.BASE_DIR)
        self._setup_styles()

    def _setup_styles(self):
        self.styles = getSampleStyleSheet()
        F, FB = self.font, self.font_bold

        self.styles.add(ParagraphStyle('DocTitle',
            fontName=FB, fontSize=20, textColor=WHITE,
            alignment=TA_CENTER, spaceAfter=6))
        self.styles.add(ParagraphStyle('DocSubtitle',
            fontName=F, fontSize=11, textColor=colors.HexColor('#cfe2ff'),
            alignment=TA_CENTER, spaceAfter=0))
        self.styles.add(ParagraphStyle('SectionHead',
            fontName=FB, fontSize=13, textColor=DARK,
            spaceBefore=14, spaceAfter=8,
            borderPad=0))
        self.styles.add(ParagraphStyle('Body',
            fontName=F, fontSize=10, textColor=colors.HexColor('#333333'),
            spaceAfter=4, leading=14))
        self.styles.add(ParagraphStyle('BodyBold',
            fontName=FB, fontSize=10, textColor=DARK,
            spaceAfter=4, leading=14))
        self.styles.add(ParagraphStyle('Small',
            fontName=F, fontSize=8.5, textColor=colors.HexColor('#6c757d'),
            spaceAfter=2))
        self.styles.add(ParagraphStyle('ScoreBig',
            fontName=FB, fontSize=46, alignment=TA_CENTER, spaceAfter=0))
        self.styles.add(ParagraphStyle('ScoreLabel',
            fontName=F, fontSize=11, alignment=TA_CENTER,
            textColor=colors.HexColor('#555555'), spaceAfter=4))

    # ──────────────────────────────────────────────────────────────
    # Публичный метод
    # ──────────────────────────────────────────────────────────────
    def generate_report_response(self, user_id: int, period: str) -> BytesIO:
        user     = User.objects.get(id=user_id)
        kpi_data = self.calculator.calculate_dashboard(user_id, period)
        history  = self.calculator.get_user_kpi_history(user_id, months=6)
        recs     = self.calculator.generate_recommendations(user_id, period)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=1.8*cm, leftMargin=1.8*cm,
            topMargin=1.5*cm, bottomMargin=1.8*cm,
            title=f'KPI Отчёт — {user.get_full_name() or user.username}',
        )

        story = []
        story += self._header_banner(user, period, kpi_data)
        story += self._summary_table(kpi_data)
        story += self._groups_section(kpi_data)
        story += self._history_section(history)
        if recs:
            story += self._recommendations_section(recs)
        story += self._footer_note()

        doc.build(story)
        buffer.seek(0)
        return buffer

    # ──────────────────────────────────────────────────────────────
    # Секции PDF
    # ──────────────────────────────────────────────────────────────
    def _header_banner(self, user, period, kpi_data):
        score = kpi_data['total_score']
        level = kpi_data['performance_level']
        bonus = kpi_data['bonus_amount']

        # Синяя шапка через таблицу (растянута на всю ширину)
        title_para   = Paragraph('ОТЧЁТ ПО KPI', self.styles['DocTitle'])
        sub_para     = Paragraph(
            f'{user.get_full_name() or user.username} &nbsp;·&nbsp; {self._fmt_period(period)} '
            f'&nbsp;·&nbsp; Сформирован: {datetime.now().strftime("%d.%m.%Y")}',
            self.styles['DocSubtitle']
        )
        header_table = Table([[title_para], [sub_para]], colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BLUE),
            ('TOPPADDING', (0,0), (-1,-1), 18),
            ('BOTTOMPADDING', (0,0), (-1,-1), 18),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('ROUNDEDCORNERS', [6]),
        ]))

        # Три блока: балл | уровень | премия
        score_color = _score_color(score)
        score_para = Paragraph(f'<font color="{score_color.hexval()}">{score:.1f}</font>',
                               self.styles['ScoreBig'])
        score_lbl  = Paragraph('Балл KPI', self.styles['ScoreLabel'])

        level_text = self._fmt_level(level)
        level_para = Paragraph(f'<b>{level_text}</b>', self.styles['BodyBold'])
        level_lbl  = Paragraph('Уровень эффективности', self.styles['Small'])

        bonus_para = Paragraph(f'<b>{bonus:,.0f} ₽</b>', self.styles['BodyBold'])
        bonus_lbl  = Paragraph('Потенциальная премия', self.styles['Small'])

        kpi_cells = [
            [score_para, level_para, bonus_para],
            [score_lbl,  level_lbl,  bonus_lbl],
        ]
        kpi_table = Table(kpi_cells, colWidths=[5.5*cm, 6*cm, 5.5*cm])
        kpi_table.setStyle(TableStyle([
            ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',   (0,0), (-1,-1), 10),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
            ('LINEAFTER',    (0,0), (1,-1), 1, GRAY_LINE),
            ('BACKGROUND',   (0,0), (-1,-1), GRAY_BG),
            ('ROUNDEDCORNERS', [4]),
        ]))

        return [
            header_table,
            Spacer(1, 0.5*cm),
            kpi_table,
            Spacer(1, 0.6*cm),
            HRFlowable(width='100%', thickness=1, color=GRAY_LINE),
            Spacer(1, 0.4*cm),
        ]

    def _summary_table(self, kpi_data):
        elements = [Paragraph('1. Сводная информация', self.styles['SectionHead'])]

        rows = [
            [Paragraph('<b>Показатель</b>', self.styles['Body']),
             Paragraph('<b>Значение</b>', self.styles['Body'])],
            ['Итоговый балл KPI', f"{kpi_data['total_score']:.1f}%"],
            ['Уровень эффективности', self._fmt_level(kpi_data['performance_level'])],
            ['Премиальная выплата', f"{kpi_data['bonus_amount']:,.0f} ₽"],
        ]

        t = Table(rows, colWidths=[9*cm, 8*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), DARK),
            ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
            ('FONTNAME',      (0,0), (-1,0), self.font_bold),
            ('FONTNAME',      (0,1), (-1,-1), self.font),
            ('FONTSIZE',      (0,0), (-1,-1), 10),
            ('ALIGN',         (1,0), (1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
            ('GRID',          (0,0), (-1,-1), 0.5, GRAY_LINE),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ]))
        elements += [t, Spacer(1, 0.5*cm)]
        return elements

    def _groups_section(self, kpi_data):
        elements = [Paragraph('2. Детализация по группам показателей', self.styles['SectionHead'])]

        for group_data in kpi_data['group_scores'].values():
            g_score = group_data['score']
            g_color = _score_color(g_score)

            # Строка заголовка группы
            group_header = Table(
                [[Paragraph(f"<b>{group_data['name']}</b>", self.styles['BodyBold']),
                  Paragraph(f"<font color='{g_color.hexval()}'><b>{g_score:.1f}%</b></font>",
                            self.styles['BodyBold'])]],
                colWidths=[13*cm, 4*cm]
            )
            group_header.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,-1), GRAY_BG),
                ('TOPPADDING',    (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
                ('ALIGN',         (1,0), (1,-1), 'RIGHT'),
                ('RIGHTPADDING',  (1,0), (1,-1), 10),
                ('LINEBELOW',     (0,0), (-1,-1), 2, g_color),
            ]))
            elements.append(group_header)

            # Строки показателей
            ind_rows = [
                [Paragraph('<b>Показатель</b>', self.styles['Small']),
                 Paragraph('<b>Факт</b>', self.styles['Small']),
                 Paragraph('<b>План</b>', self.styles['Small']),
                 Paragraph('<b>Выполнение</b>', self.styles['Small'])],
            ]
            for ind in group_data['indicators']:
                pct = ind['completion_percent']
                pct_str = f"{pct:.1f}%"
                ind_rows.append([
                    Paragraph(ind['name'], self.styles['Body']),
                    f"{ind['actual_value']:.1f} {ind.get('unit', '')}".strip(),
                    f"{ind['target_value']:.1f} {ind.get('unit', '')}".strip(),
                    Paragraph(f"<font color='{_score_color(pct).hexval()}'><b>{pct_str}</b></font>",
                              self.styles['Body']),
                ])

            ind_table = Table(ind_rows, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
            ind_table.setStyle(TableStyle([
                ('BACKGROUND',    (0,0), (-1,0), colors.HexColor('#495057')),
                ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
                ('FONTNAME',      (0,0), (-1,0), self.font_bold),
                ('FONTNAME',      (0,1), (-1,-1), self.font),
                ('FONTSIZE',      (0,0), (-1,-1), 9),
                ('ALIGN',         (1,0), (-1,-1), 'CENTER'),
                ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
                ('GRID',          (0,0), (-1,-1), 0.4, GRAY_LINE),
                ('TOPPADDING',    (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            elements += [ind_table, Spacer(1, 0.5*cm)]

        return elements

    def _history_section(self, history):
        elements = [Paragraph('3. Динамика KPI за последние 6 месяцев', self.styles['SectionHead'])]

        rows = [
            [Paragraph(f'<b>{h}</b>', self.styles['Small']) for h in
             ['Период', 'Балл KPI', 'Уровень эффективности', 'Премия']],
        ]
        for item in history:
            sc = item['total_score']
            rows.append([
                self._fmt_period(item['period']),
                Paragraph(f"<font color='{_score_color(sc).hexval()}'><b>{sc:.1f}%</b></font>",
                          self.styles['Body']),
                self._fmt_level(item['performance_level']),
                f"{item['bonus_amount']:,.0f} ₽",
            ])

        t = Table(rows, colWidths=[4*cm, 4*cm, 5*cm, 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,0), DARK),
            ('TEXTCOLOR',     (0,0), (-1,0), WHITE),
            ('FONTNAME',      (0,0), (-1,0), self.font_bold),
            ('FONTNAME',      (0,1), (-1,-1), self.font),
            ('FONTSIZE',      (0,0), (-1,-1), 9),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1), (-1,-1), [WHITE, GRAY_BG]),
            ('GRID',          (0,0), (-1,-1), 0.4, GRAY_LINE),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements += [t, Spacer(1, 0.5*cm)]
        return elements

    def _recommendations_section(self, recs):
        elements = [
            HRFlowable(width='100%', thickness=1, color=GRAY_LINE),
            Spacer(1, 0.3*cm),
            Paragraph('4. Рекомендации по улучшению показателей', self.styles['SectionHead']),
        ]
        for i, rec in enumerate(recs, 1):
            elements.append(Paragraph(
                f'<b>{i}. {rec["indicator_name"]}</b> — текущее выполнение: {rec["current_completion"]:.1f}%',
                self.styles['BodyBold']
            ))
            elements.append(Paragraph(rec['text'], self.styles['Body']))
            elements.append(Paragraph(
                f'Целевое значение: {rec["target_value"]:.1f} · Срок: {self._fmt_period(rec["deadline_period"])}',
                self.styles['Small']
            ))
            elements.append(Spacer(1, 0.3*cm))
        return elements

    def _footer_note(self):
        return [
            Spacer(1, 0.4*cm),
            HRFlowable(width='100%', thickness=0.5, color=GRAY_LINE),
            Paragraph(
                f'Документ сформирован автоматически системой управления KPI · {datetime.now().strftime("%d.%m.%Y %H:%M")}',
                self.styles['Small']
            ),
        ]

    # ──────────────────────────────────────────────────────────────
    # Хелперы
    # ──────────────────────────────────────────────────────────────
    def _fmt_period(self, period: str) -> str:
        months = {'01':'Январь','02':'Февраль','03':'Март','04':'Апрель',
                  '05':'Май','06':'Июнь','07':'Июль','08':'Август',
                  '09':'Сентябрь','10':'Октябрь','11':'Ноябрь','12':'Декабрь'}
        try:
            year, month = period.split('-')
            return f"{months[month]} {year}"
        except Exception:
            return period

    def _fmt_level(self, level: str) -> str:
        return {'высокий':'Высокая эффективность',
                'средний':'Средняя эффективность',
                'низкий':'Низкая эффективность'}.get(level, level)

    # ──────────────────────────────────────────────────────────────
    # Excel экспорт
    # ──────────────────────────────────────────────────────────────
    def generate_excel_response(self, user_id: int, period: str) -> BytesIO:
        from openpyxl import Workbook
        from openpyxl.styles import (
            Font, PatternFill, Alignment, Border, Side, numbers
        )
        from openpyxl.utils import get_column_letter

        user     = User.objects.get(id=user_id)
        kpi_data = self.calculator.calculate_dashboard(user_id, period)
        history  = self.calculator.get_user_kpi_history(user_id, months=6)
        recs     = self.calculator.generate_recommendations(user_id, period)

        wb = Workbook()

        # ── Лист 1: Сводка ──────────────────────────────────────
        ws1 = wb.active
        ws1.title = 'Сводка'

        # Стили
        hdr_font    = Font(bold=True, color='FFFFFF', size=12)
        hdr_fill    = PatternFill('solid', fgColor='1A73E8')
        sub_font    = Font(bold=True, size=11, color='1E2A38')
        center      = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left        = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin        = Side(style='thin', color='DEE2E6')
        border      = Border(left=thin, right=thin, top=thin, bottom=thin)
        gray_fill   = PatternFill('solid', fgColor='F5F7FA')

        def hdr_row(ws, row, values, col_start=1):
            for i, v in enumerate(values):
                c = ws.cell(row=row, column=col_start+i, value=v)
                c.font = hdr_font; c.fill = hdr_fill
                c.alignment = center; c.border = border

        def data_row(ws, row, values, col_start=1, bold=False, fill=None):
            for i, v in enumerate(values):
                c = ws.cell(row=row, column=col_start+i, value=v)
                c.font = Font(bold=bold, size=10)
                c.alignment = left; c.border = border
                if fill: c.fill = fill

        # Заголовок листа
        ws1.merge_cells('A1:C1')
        title_cell = ws1['A1']
        title_cell.value = f'Отчёт KPI — {user.get_full_name() or user.username} — {self._fmt_period(period)}'
        title_cell.font  = Font(bold=True, size=14, color='1A73E8')
        title_cell.alignment = center
        ws1.row_dimensions[1].height = 30

        ws1.cell(row=2, column=1, value=f'Сформирован: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
        ws1.cell(row=2, column=1).font = Font(size=9, color='6C757D')

        # Сводная таблица
        hdr_row(ws1, 4, ['Показатель', 'Значение', 'Комментарий'])
        score = kpi_data['total_score']
        data_row(ws1, 5, ['Итоговый балл KPI', f"{score:.1f}%",
                          'Отлично' if score>=90 else ('Хорошо' if score>=70 else 'Требует улучшения')])
        data_row(ws1, 6, ['Уровень эффективности', self._fmt_level(kpi_data['performance_level']), ''],
                 fill=gray_fill)
        data_row(ws1, 7, ['Премиальная выплата', f"{kpi_data['bonus_amount']:,.0f} ₽", ''])

        ws1.column_dimensions['A'].width = 30
        ws1.column_dimensions['B'].width = 22
        ws1.column_dimensions['C'].width = 28

        # ── Лист 2: Показатели ──────────────────────────────────
        ws2 = wb.create_sheet('Показатели по группам')

        hdr_row(ws2, 1, ['Группа', 'Показатель', 'Факт', 'План', 'Единица', 'Выполнение %', 'Статус'])
        r = 2
        for group_data in kpi_data['group_scores'].values():
            for ind in group_data['indicators']:
                pct = ind['completion_percent']
                status = 'Выполнено' if pct >= 100 else ('В норме' if pct >= 70 else 'Не выполнено')
                row_fill = gray_fill if r % 2 == 0 else None
                data_row(ws2, r, [
                    group_data['name'],
                    ind['name'],
                    round(ind['actual_value'], 2),
                    round(ind['target_value'], 2),
                    ind.get('unit', ''),
                    round(pct, 1),
                    status,
                ], fill=row_fill)
                # Цвет колонки "Выполнение"
                pct_cell = ws2.cell(row=r, column=6)
                if pct >= 90:
                    pct_cell.fill = PatternFill('solid', fgColor='D4EDDA')
                    pct_cell.font = Font(color='155724', bold=True)
                elif pct >= 70:
                    pct_cell.fill = PatternFill('solid', fgColor='FFF3CD')
                    pct_cell.font = Font(color='856404', bold=True)
                else:
                    pct_cell.fill = PatternFill('solid', fgColor='F8D7DA')
                    pct_cell.font = Font(color='721C24', bold=True)
                r += 1

        for col, w in zip(['A','B','C','D','E','F','G'], [22, 32, 10, 10, 12, 14, 14]):
            ws2.column_dimensions[col].width = w

        # ── Лист 3: История ─────────────────────────────────────
        ws3 = wb.create_sheet('История KPI')
        hdr_row(ws3, 1, ['Период', 'Балл KPI (%)', 'Уровень эффективности', 'Премия (₽)'])
        for i, item in enumerate(history, 2):
            fill = gray_fill if i % 2 == 0 else None
            data_row(ws3, i, [
                self._fmt_period(item['period']),
                round(item['total_score'], 1),
                self._fmt_level(item['performance_level']),
                round(item['bonus_amount'], 0),
            ], fill=fill)
        for col, w in zip(['A','B','C','D'], [20, 14, 26, 16]):
            ws3.column_dimensions[col].width = w

        # ── Лист 4: Рекомендации ────────────────────────────────
        if recs:
            ws4 = wb.create_sheet('Рекомендации')
            hdr_row(ws4, 1, ['Показатель', 'Текущее выполнение %', 'Рекомендация', 'Целевое значение', 'Срок'])
            for i, rec in enumerate(recs, 2):
                fill = gray_fill if i % 2 == 0 else None
                data_row(ws4, i, [
                    rec['indicator_name'],
                    round(rec['current_completion'], 1),
                    rec['text'],
                    rec['target_value'],
                    self._fmt_period(rec['deadline_period']),
                ], fill=fill)
            for col, w in zip(['A','B','C','D','E'], [26, 20, 48, 16, 16]):
                ws4.column_dimensions[col].width = w

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer

    # Оставляем совместимость
    def generate_user_report(self, user_id: int, period: str) -> str:
        return self.generate_report_response(user_id, period)
