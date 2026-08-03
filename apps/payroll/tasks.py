"""
apps/payroll/tasks.py

Celery tasks untuk operasi payroll berat yang tidak boleh dijalankan
sinkron dalam siklus request-response (akan timeout untuk 1000+ karyawan).
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='payroll.calculate_period')
def calculate_payroll_period_task(self, period_id: int):
    """
    Hitung payroll untuk semua karyawan aktif dalam satu periode.

    Dipanggil via .delay(period.id) dari PayrollPeriodViewSet.calculate().
    Berjalan di Celery Worker — tidak memblokir request web sama sekali.
    Status dapat dipantau lewat endpoint GET /periods/{id}/items/.
    """
    from .models import PayrollPeriod
    from .calculator import calculate_payroll_item
    from apps.employees.models import Employee

    try:
        period = PayrollPeriod.objects.get(id=period_id)
    except PayrollPeriod.DoesNotExist:
        logger.error('[calculate_period] PayrollPeriod id=%s tidak ditemukan.', period_id)
        return {'success': False, 'error': 'Period tidak ditemukan'}

    employees = Employee.objects.filter(entity=period.entity, status=Employee.Status.ACTIVE)
    calculated, errors = 0, []

    for emp in employees:
        try:
            calculate_payroll_item(period, emp)
            calculated += 1
        except Exception as exc:
            error_msg = str(exc)
            errors.append({'employee': emp.full_name, 'employee_id': emp.employee_id, 'error': error_msg})
            logger.warning(
                '[calculate_period] Gagal hitung payroll karyawan %s (%s): %s',
                emp.full_name, emp.employee_id, error_msg,
            )

    # Update status kembali ke DRAFT setelah kalkulasi selesai
    period.status = PayrollPeriod.Status.DRAFT
    period.save(update_fields=['status'])

    logger.info(
        '[calculate_period] Period id=%s selesai: %d karyawan berhasil, %d error.',
        period_id, calculated, len(errors),
    )
    return {'success': True, 'calculated': calculated, 'errors': errors}
