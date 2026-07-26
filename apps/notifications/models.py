from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        CONTRACT_EXPIRING = 'CONTRACT_EXPIRING', 'Kontrak Mau Habis'
        LEAVE_APPROVAL = 'LEAVE_APPROVAL', 'Persetujuan Cuti'
        PAYROLL_READY = 'PAYROLL_READY', 'Slip Gaji Tersedia'
        SYSTEM = 'SYSTEM', 'Sistem'

    recipient = models.ForeignKey(
        'core.User', on_delete=models.CASCADE,
        related_name='notifications', verbose_name='Penerima'
    )
    title = models.CharField(max_length=255, verbose_name='Judul')
    message = models.TextField(verbose_name='Pesan')
    notification_type = models.CharField(
        max_length=25, choices=Type.choices,
        default=Type.SYSTEM, verbose_name='Tipe'
    )
    is_read = models.BooleanField(default=False, verbose_name='Sudah Dibaca')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.recipient.email} — {self.title}'
