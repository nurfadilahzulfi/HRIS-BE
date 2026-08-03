"""
apps/employees/signals.py — FIX untuk temuan audit:
"Tidak ada sinkronisasi antara Employee.status=TERMINATED dan User.is_active"
dan "terminate() action tidak menonaktifkan akun login".

Signal ini memastikan: begitu status karyawan berubah jadi TERMINATED atau
INACTIVE (lewat jalur MANAPUN -- admin, API, script, bukan cuma lewat
action terminate() di views.py), akun login-nya OTOMATIS dinonaktifkan dan
semua refresh token yang beredar di-blacklist. Ini pertahanan berlapis:
jangan cuma andalkan views.py melakukan ini secara eksplisit, karena ada
banyak jalur lain (Django Admin bulk action, management command, dsb) yang
bisa mengubah status tanpa lewat endpoint API.

WAJIB didaftarkan di apps.py (lihat apps_ready_snippet.py di folder ini)
supaya signal ini aktif saat Django startup.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Employee

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Employee)
def deactivate_user_on_termination(sender, instance: Employee, **kwargs) -> None:
    """
    Saat status karyawan berubah jadi TERMINATED/INACTIVE, nonaktifkan
    akun login-nya dan blacklist semua refresh token yang masih beredar.
    """
    if instance.status not in (Employee.Status.TERMINATED, Employee.Status.INACTIVE):
        return

    user = getattr(instance, 'user', None)
    if not user:
        return

    if user.is_active:
        user.is_active = False
        user.save(update_fields=['is_active'])
        logger.info(
            'User %s dinonaktifkan otomatis karena Employee %s berstatus %s',
            user.email, instance.employee_id, instance.status,
        )

    _blacklist_all_tokens(user)


def _blacklist_all_tokens(user) -> None:
    """
    Blacklist semua refresh token milik user ini, supaya sesi yang sudah
    terlanjur login (termasuk token yang mungkin masih dipegang orang lain
    kalau akun sempat dibajak) langsung mati, bukan menunggu expired alami.
    Gagal-aman: kalau django-rest-framework-simplejwt token_blacklist app
    belum terpasang, cukup log warning, jangan sampai proses terminate
    gagal gara-gara ini.
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken, OutstandingToken,
        )
    except ImportError:
        logger.warning(
            'token_blacklist app tidak terpasang -- token JWT user %s TIDAK di-blacklist otomatis.',
            user.email,
        )
        return

    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(token=token)

    if outstanding_tokens.exists():
        logger.info('%d token milik user %s berhasil di-blacklist.', outstanding_tokens.count(), user.email)
