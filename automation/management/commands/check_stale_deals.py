from django.core.management.base import BaseCommand

from automation.engine import run_stale_deal_check


class Command(BaseCommand):
    help = (
        "Проверяет правила автоматизации с триггером «нет активности N дней» "
        "и применяет их действия к зависшим сделкам. Предполагается периодический "
        "запуск (cron / Планировщик заданий Windows)."
    )

    def handle(self, *args, **options):
        triggered = run_stale_deal_check()
        self.stdout.write(self.style.SUCCESS(f"Сработало правил: {triggered}"))
