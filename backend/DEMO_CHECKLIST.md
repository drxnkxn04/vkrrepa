# Чеклист

## 1) Разовая настройка окружения

```powershell
cd backend
python manage.py migrate
python manage.py prepare_demo_workflow
```

Demo accounts created by command:
- employee: `demo_employee` / `demo12345`
- manager: `demo_manager` / `demo12345`

## 2) Запуск бэкенда и фронтенда

Backend:

```powershell
cd backend
python manage.py runserver
```

Frontend:

```powershell
cd frontend
npm install
npm run serve
```

## 3) Сценарий демонстрации

1. Вход под ролью сотрудника (demo_employee).
2. Переход в дашборд, добавление/обновление значения KPI (сохранение как черновик).
3. Отправка значения KPI на проверку менеджеру.
4. Выход из системы.
5. Вход под ролью менеджера (demo_manager).
6. Переход в панель менеджера / список заявок на проверку 
7. Утверждение значения (или отклонение для показа альтернативного пути).
8. Выход из системы.
9. Повторный вход под ролью сотрудника.
10. Проверка дашборда за текущий период: показ обновленного итогового балла KPI.
11. Демонстрация графика истории изменений.
12. Генерация PDF-отчета.

## 4) Быстрый сброс данных перед повторным показом

```powershell
cd backend
python manage.py prepare_demo_workflow
```

## 5) Валидация (запуск тестов)

```powershell
cd backend
python manage.py test apps.kpi.tests.test_defense_flow apps.kpi.tests.test_api_workflow
```
