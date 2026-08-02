from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Employee


@receiver(post_save, sender=Employee)
def deactivate_user_on_termination(sender, instance: Employee, **kwargs) -> None:
    """
    Saat status karyawan berubah jadi TERMINATED/INACTIVE, nonaktifkan
    akun login-nya otomatis. Ini krusial untuk keamanan -- jangan
    andalkan HR admin ingat untuk menonaktifkan akun secara manual.
    """
    if instance.status in (Employee.Status.TERMINATED, Employee.Status.INACTIVE):
        user = getattr(instance, 'user', None)
        if user and user.is_active:
            user.is_active = False
            user.save(update_fields=['is_active'])
