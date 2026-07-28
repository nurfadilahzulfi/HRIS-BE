import logging
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(name='notifications.check_birthdays')
def check_birthdays():
    """
    Dijalankan setiap hari pukul 07:00.
    Kirim email ucapan ulang tahun ke karyawan & notifikasi ke HR.
    """
    from apps.employees.models import Employee

    today = timezone.now().date()
    birthday_employees = Employee.objects.filter(
        status=Employee.Status.ACTIVE,
        date_of_birth__month=today.month,
        date_of_birth__day=today.day,
    ).select_related('entity')

    sent_count = 0
    for emp in birthday_employees:
        user = getattr(emp, 'user_account', None)
        email = user.email if user else None
        if email:
            subject = f'Selamat Ulang Tahun, {emp.full_name}! 🎉'
            message = (
                f'Halo {emp.full_name},\n\n'
                f'Seluruh keluarga besar {emp.entity.name} mengucapkan Selamat Ulang Tahun!\n'
                f'Semoga sukses, sehat, dan bahagia selalu.\n\n'
                f'Salam hangat,\nHR Department'
            )
            try:
                send_mail(
                    subject, message,
                    settings.DEFAULT_FROM_EMAIL, [email],
                    fail_silently=True
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending birthday email to {emp.full_name}: {e}")

    logger.info(f"Sent {sent_count} birthday greetings.")
    return {'sent': sent_count}


@shared_task(name='notifications.check_contract_expiry')
def check_contract_expiry():
    """
    Dijalankan setiap hari pukul 08:00.
    Kirim email alert jika kontrak karyawan (PKWT) berakhir dalam 30, 14, atau 7 hari.
    """
    from apps.contracts.models import Contract

    today = timezone.now().date()
    target_days = [30, 14, 7]
    alerts_sent = 0

    for days in target_days:
        target_date = today + timezone.timedelta(days=days)
        expiring_contracts = Contract.objects.filter(
            status=Contract.Status.ACTIVE,
            contract_type=Contract.ContractType.PKWT,
            end_date=target_date,
        ).select_related('employee__entity', 'employee__manager')

        for contract in expiring_contracts:
            emp = contract.employee
            manager_email = None
            if emp.manager and hasattr(emp.manager, 'user_account'):
                manager_email = emp.manager.user_account.email

            subject = f'[ALERT] Kontrak Karyawan Berakhir dalam {days} Hari — {emp.full_name}'
            message = (
                f'Informasi Masa Berakhir Kontrak:\n\n'
                f'Nama Karyawan : {emp.full_name} ({emp.employee_id})\n'
                f'Entitas       : {emp.entity.name}\n'
                f'Tanggal Akhir : {contract.end_date}\n'
                f'Sisa Hari     : {days} hari\n\n'
                f'Mohon lakukan tindak lanjut perpanjangan atau pengakhiran kontrak di sistem HRIS.'
            )

            recipients = []
            if manager_email:
                recipients.append(manager_email)
            if hasattr(settings, 'HR_NOTIFICATION_EMAIL') and settings.HR_NOTIFICATION_EMAIL:
                recipients.append(settings.HR_NOTIFICATION_EMAIL)

            if recipients:
                try:
                    send_mail(
                        subject, message,
                        settings.DEFAULT_FROM_EMAIL, recipients,
                        fail_silently=True
                    )
                    alerts_sent += 1
                except Exception as e:
                    logger.error(f"Error sending contract alert for {emp.full_name}: {e}")

    logger.info(f"Sent {alerts_sent} contract expiry alerts.")
    return {'alerts_sent': alerts_sent}


@shared_task(name='notifications.remind_pending_approvals')
def remind_pending_approvals():
    """
    Dijalankan setiap hari pukul 09:00.
    Kirim email pengingat untuk persetujuan cuti yang masih pending > 24 jam.
    """
    from apps.leave.models import LeaveApproval

    cutoff_time = timezone.now() - timezone.timedelta(hours=24)
    pending_approvals = LeaveApproval.objects.filter(
        status=LeaveApproval.Status.PENDING,
        leave_request__submitted_at__lte=cutoff_time,
    ).select_related('approver', 'leave_request__employee')

    reminders_sent = 0
    for appr in pending_approvals:
        approver_emp = appr.approver
        user = getattr(approver_emp, 'user_account', None)
        email = user.email if user else None
        if email:
            req = appr.leave_request
            subject = f'[REMINDER] Permohonan Cuti Menunggu Persetujuan Anda — {req.employee.full_name}'
            message = (
                f'Yth. {approver_emp.full_name},\n\n'
                f'Anda memiliki permohonan cuti yang belum disetujui:\n'
                f'Karyawan  : {req.employee.full_name}\n'
                f'Jenis Cuti : {req.leave_type.name}\n'
                f'Tanggal    : {req.start_date} s/d {req.end_date} ({req.total_days} hari)\n'
                f'Alasan     : {req.reason}\n\n'
                f'Mohon login ke HRIS portal untuk memberikan persetujuan.'
            )
            try:
                send_mail(
                    subject, message,
                    settings.DEFAULT_FROM_EMAIL, [email],
                    fail_silently=True
                )
                reminders_sent += 1
            except Exception as e:
                logger.error(f"Error sending leave approval reminder to {approver_emp.full_name}: {e}")

    logger.info(f"Sent {reminders_sent} leave approval reminders.")
    return {'reminders_sent': reminders_sent}
