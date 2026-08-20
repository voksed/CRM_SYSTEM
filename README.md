# CRM System

**English** · [Русский](README.ru.md)

**Django + vanilla JS/CSS open-source CRM for the CIS market** — contacts, a Kanban deals pipeline, tasks, billing, role-based access, an automation engine, Telegram integration, and full audit logging. No frontend framework, no build step, no bloat.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Django](https://img.shields.io/badge/django-5.2-0C4B33)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Why this exists

Most CRM tutorials stop at "add a contact." This one goes further: leads move through a real sales pipeline, managers only ever see their own data, actions get logged, and a rule engine reacts to what happens in the pipeline — all built with a server-rendered Django backend and plain JavaScript on the frontend, no React/Vue/build tooling required.

## Features

- **Contacts & leads** — source, status, tags, assigned manager, full communication timeline per contact
- **Kanban deals pipeline** — drag-and-drop between stages using the native HTML5 Drag & Drop API, no JS libraries
- **Tasks** — due dates, overdue highlighting, auto-generated follow-ups from automation rules
- **Billing** — invoices with shareable public payment links, manual payment recording, running balance per deal
- **Role-based access** — Owner sees and manages everything; Managers are scoped to their own contacts/deals/tasks at the query level, not just hidden in the UI
- **Automation engine** — configurable triggers (stage changed, payment received, no activity for N days) → actions (create task, move stage, log event)
- **Telegram integration** — a real bot connection built on [aiogram](https://github.com/aiogram/aiogram); incoming messages from unknown chats automatically create a new lead (webhook + long-polling command included), configured from an in-app settings page — no admin panel required
- **Audit log** — every login (success/failure with IP), every create/update/delete/move, attributed to the acting user and timestamped
- **Light/dark theme**, generated strong passwords for new accounts, brute-force login protection

## Tech stack

| Layer | Choice |
| --- | --- |
| Backend | Django 5.2, Django REST Framework |
| Frontend | Vanilla JavaScript (`fetch`, native Drag & Drop), plain CSS with custom properties for theming |
| Database | SQLite by default — swap the `DATABASES` setting for Postgres/MySQL in production |
| Auth | Django's built-in auth + a custom `User` model, rate-limited login |
| Messaging | [aiogram](https://github.com/aiogram/aiogram) 3.x (async), bridged into Django's sync views/commands via `asgiref` |
| Config | `python-dotenv` — secrets and environment-specific settings live in a local `.env`, never committed |

## Getting started

### Prerequisites
- Python 3.11+

### Installation

```bash
git clone https://github.com/voksed/CRM_SYSTEM.git
cd CRM_SYSTEM

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file in the project root (never committed — it's gitignored):

```bash
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
TELEGRAM_BOT_TOKEN=
```

Generate a real secret key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open **http://127.0.0.1:8000/** and log in with the superuser you just created — an organization and a default sales pipeline are created automatically on first login.

### Telegram integration (optional)

1. Create a bot with [@BotFather](https://t.me/BotFather) and grab its token.
2. In the app, go to **Telegram** in the sidebar (Owner only) and paste the token — it's verified live against the Telegram API and the bot's username is shown once connected. (Optionally set `TELEGRAM_BOT_TOKEN` in `.env` to pre-fill this field.)
3. Start receiving messages:

   ```bash
   python manage.py run_telegram_bot
   ```

   This runs an aiogram long-polling process that keeps listening until stopped (`Ctrl+C`). Messages from chats not yet linked to a contact automatically create a new lead. For production, use the included webhook endpoint (`channels_app.views.telegram_webhook`) instead of polling.

## Project layout

```
accounts/       organizations, users, roles, permissions
contacts/       leads/contacts, tags
deals/          pipelines, stages, deals
tasks/          task management
billing/        invoices & payments
automation/     rule engine (triggers → actions)
channels_app/   messaging channels (Telegram) + communication timeline
audit/          audit log (who did what, when, from where)
config/         Django project settings & root URLs
```

## Roles

| | Owner | Manager |
| --- | --- | --- |
| View all contacts/deals/tasks in the org | ✅ | ❌ (own only) |
| Reassign records to other managers | ✅ | ❌ |
| Automation rules | ✅ | ❌ |
| Team management | ✅ | ❌ |
| Audit log | ✅ | ❌ |
| Analytics | Full, cross-team | Personal only |

## License

MIT — see [LICENSE](LICENSE).
