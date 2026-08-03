"""
apps/contracts/tasks.py

Celery scheduled tasks untuk manajemen kontrak.
Dijalankan otomatis oleh Celery Beat — TIDAK mempengaruhi performa request-response.

Task ini berjalan di proses Celery Worker yang terpisah dari Django web server,
sehingga 300 user request bersamaan tidak terdampak sama sekali.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='contracts.expire_contracts')
def expire_expired_contracts(self):
    """
    Cek semua kontrak dengan status ACTIVE yang end_date-nya sudah lewat hari ini,
    lalu ubah statusnya menjadi EXPIRED secara bulk.

    Dijadwalkan harian via Celery Beat (lihat CELERY_BEAT_SCHEDULE di settings).
    Menggunakan bulk_update agar efisien — 1 query UPDATE meski ada ribuan kontrak.
    """
    from .models import Contract

    today = timezone.now().date()

    # Cari semua kontrak ACTIVE yang sudah melewati end_date
    # PKWTT tidak punya end_date (null) — dikecualikan otomatis oleh filter ini
    expired_qs = Contract.objects.filter(
        status=Contract.Status.ACTIVE,
        end_date__isnull=False,
        end_date__lt=today,
    )

    count = expired_qs.count()
    if count == 0:
        logger.info('[expire_contracts] Tidak ada kontrak yang perlu di-expire.')
        return {'expired': 0}

    # Bulk update — satu query untuk semua, bukan loop per objek
    expired_qs.update(status=Contract.Status.EXPIRED)

    logger.info(
        '[expire_contracts] %d kontrak berhasil di-set EXPIRED (cutoff: %s).',
        count, today,
    )
    return {'expired': count}
