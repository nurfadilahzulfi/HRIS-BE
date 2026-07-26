from celery import shared_task
from .generator import generate_slip_pdf


@shared_task(name='salary_slip.generate_for_period')
def generate_salary_slips_for_period(period_id: int):
    """
    Dipanggil saat payroll FINALIZED.
    Generate PDF slip gaji untuk semua PayrollItem dalam periode.
    """
    from apps.payroll.models import PayrollItem
    items = PayrollItem.objects.filter(
        period_id=period_id
    ).select_related('employee', 'period__entity')

    generated = 0
    errors    = []

    for item in items:
        try:
            generate_slip_pdf(item)
            generated += 1
        except Exception as e:
            errors.append({'employee': item.employee.full_name, 'error': str(e)})

    return {'generated': generated, 'errors': errors}


@shared_task(name='salary_slip.send_emails_for_period')
def send_salary_slip_emails_for_period(period_id: int):
    """
    Kirim slip gaji via email ke setiap karyawan.
    Dipanggil H+1 setelah slip di-generate.
    """
    from django.core.mail import EmailMessage
    from django.utils import timezone
    from .models import SalarySlip
    from apps.payroll.models import PayrollPeriod

    try:
        period = PayrollPeriod.objects.get(id=period_id)
    except PayrollPeriod.DoesNotExist:
        return {'error': 'Period not found'}

    slips = SalarySlip.objects.filter(
        payroll_item__period=period,
        pdf_file__isnull=False,
        is_sent=False,
    ).select_related('payroll_item__employee')

    sent = 0
    for slip in slips:
        emp = slip.payroll_item.employee
        # Cari email dari user account karyawan
        user = getattr(emp, 'user_account', None)
        email = user.email if user else None

        if not email:
            continue

        try:
            subject = f'Slip Gaji {period.month:02d}/{period.year} — {emp.full_name}'
            body    = (
                f'Yth. {emp.full_name},\n\n'
                f'Berikut terlampir slip gaji Anda untuk periode {period.month:02d}/{period.year}.\n\n'
                f'Salam,\nHR Department'
            )
            msg = EmailMessage(subject=subject, body=body, to=[email])
            if slip.pdf_file:
                msg.attach(f'{slip.slip_number}.pdf', slip.pdf_file.read(), 'application/pdf')
            msg.send()

            slip.is_sent = True
            slip.sent_at = timezone.now()
            slip.save(update_fields=['is_sent', 'sent_at'])
            sent += 1
        except Exception:
            pass

    return {'sent': sent}
