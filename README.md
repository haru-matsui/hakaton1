# Помощник по конспектам (Conspectus Helper)

Веб-приложение для создания, публикации и совместного использования конспектов лекций с поддержкой Markdown, комментариев, рейтингов и экспорта.

## Основные возможности

### Для всех пользователей:
- 📝 Создание конспектов с Markdown-редактором (EasyMDE)
- 👀 Просмотр и поиск конспектов по названию, тегам, предметам
- ⭐ Система рейтингов (лайки/дизлайки)
- 💬 Комментирование с поддержкой вложенных ответов
- 🔖 Избранное для сохранения интересных конспектов
- 📥 Экспорт в форматы: Markdown (.md), Word (.docx)
- 🔒 Управление видимостью: публичный, по ссылке, приватный
- 📜 История версий с возможностью просмотра изменений
- 👥 Профили пользователей с аватарами и статистикой

### Для преподавателей:
- 🛡️ Панель модерации жалоб
- 🗑️ Расширенные права на удаление контента
- 👔 Специальный бадж "Преподаватель"

### Дополнительные функции:
- 🎨 Современный дизайн на Bootstrap 5
- 📱 Адаптивная верстка для всех устройств
- 🔐 Безопасная аутентификация
- 🏷️ Система тегов и категорий
- 📊 Статистика просмотров и скачиваний

## Установка и запуск

### Требования:
- Python 3.8+
- pip

### Шаги установки:

1. Клонируйте репозиторий:
```bash
git clone https://github.com/haru-matsui/hakaton1.git
cd hakaton1
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Инициализируйте базу данных:
```bash
python3 -c "from app import app, db; from models import Subject; app.app_context().push(); db.create_all(); print('Database initialized!')"
```

5. Создайте предметы по умолчанию:
```bash
python3 -c "
from app import app, db
from models import Subject

with app.app_context():
    subjects = ['Математика', 'Физика', 'Химия', 'Биология', 'История', 'Литература', 'Информатика', 'Английский язык', 'Философия', 'Экономика', 'Психология', 'Социология']
    for name in subjects:
        if not Subject.query.filter_by(name=name).first():
            db.session.add(Subject(name=name))
    db.session.commit()
    print('Subjects created!')
"
```

6. Запустите приложение:
```bash
python3 app.py
```

7. Откройте браузер и перейдите по адресу: http://localhost:5000

## Структура проекта

```
hakaton1/
├── app.py                  # Главный файл приложения Flask
├── models.py              # Модели базы данных SQLAlchemy
├── config.py              # Конфигурация приложения
├── requirements.txt       # Зависимости Python
├── templates/            # HTML-шаблоны Jinja2
│   ├── base.html        # Базовый шаблон
│   ├── login.html       # Страница входа
│   ├── register.html    # Страница регистрации
│   ├── feed.html        # Лента конспектов
│   ├── create_conspectus.html
│   ├── view_conspectus.html
│   ├── edit_conspectus.html
│   ├── profile.html
│   ├── search.html
│   ├── favorites.html
│   ├── moderation.html
│   └── conspectus_versions.html
├── static/              # Статические файлы
│   └── uploads/
│       └── avatars/    # Аватары пользователей
└── db/                 # База данных SQLite
    └── conspectus.db

```

## Технологии

### Backend:
- **Flask** 3.0.0 - веб-фреймворк
- **Flask-SQLAlchemy** 3.1.1 - ORM для работы с БД
- **Flask-Login** 0.6.3 - управление сессиями
- **Flask-WTF** 1.2.1 - формы и CSRF защита
- **SQLAlchemy** 2.0.23 - база данных
- **Markdown2** 2.4.12 - рендеринг Markdown
- **Bleach** 6.1.0 - санитизация HTML
- **WeasyPrint** 60.2 - экспорт в PDF (будущая функция)
- **python-docx** 1.1.0 - экспорт в Word

### Frontend:
- **Bootstrap 5.3** - UI фреймворк
- **Bootstrap Icons** - иконки
- **EasyMDE** 2.18.0 - Markdown редактор

## Модели данных

- **User** - пользователи (студенты и преподаватели)
- **Conspectus** - конспекты
- **ConspectusVersion** - история версий
- **Tag** - теги для категоризации
- **Subject** - предметы
- **Rating** - рейтинги (лайки/дизлайки)
- **Comment** - комментарии с вложенностью
- **Favorite** - избранное пользователей
- **CoAuthor** - соавторство (будущая функция)
- **Report** - жалобы на контент

## Авторы

Проект создан в рамках хакатона для улучшения образовательного процесса.

## Лицензия

MIT License