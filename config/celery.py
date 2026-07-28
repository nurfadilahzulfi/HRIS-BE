import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('hris')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# ─── Periodic Tasks ──────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Check and send birthday emails every day at 07:00 WIB
    'check-birthdays-daily': {
        'task': 'notifications.check_birthdays',
        'schedule': crontab(hour=7, minute=0),
    },
    # Check contract expiry every day at 08:00 WIB
    'check-contract-expiry-daily': {
        'task': 'notifications.check_contract_expiry',
        'schedule': crontab(hour=8, minute=0),
    },
    # Remind pending leave approvals every day at 09:00 WIB
    'remind-pending-approvals-daily': {
        'task': 'notifications.remind_pending_approvals',
        'schedule': crontab(hour=9, minute=0),
    },
}


app.conf.timezone = 'Asia/Jakarta'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
