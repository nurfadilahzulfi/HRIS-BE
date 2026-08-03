from django.db import models


class WorkSchedule(models.Model):
    entity         = models.ForeignKey(
        'company.Entity',
        on_delete=models.CASCADE,
        related_name='work_schedules',
        verbose_name='Entitas',
    )
    name           = models.CharField(max_length=100, verbose_name='Nama Shift')
    work_start     = models.TimeField(verbose_name='Jam Mulai Kerja')
    work_end       = models.TimeField(verbose_name='Jam Selesai Kerja')
    break_duration = models.PositiveSmallIntegerField(default=60, verbose_name='Durasi Istirahat (menit)')
    is_active      = models.BooleanField(default=True, verbose_name='Aktif')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Work Schedule'
        verbose_name_plural = 'Work Schedules'
        ordering            = ['name']

    def __str__(self):
        return f'{self.name} ({self.work_start}–{self.work_end})'


class EmployeeSchedule(models.Model):
    employee       = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Karyawan',
    )
    schedule       = models.ForeignKey(
        WorkSchedule,
        on_delete=models.CASCADE,
        related_name='employee_schedules',
        verbose_name='Shift',
    )
    effective_from = models.DateField(verbose_name='Berlaku Mulai')
    effective_to   = models.DateField(null=True, blank=True, verbose_name='Berlaku Sampai')

    class Meta:
        verbose_name        = 'Employee Schedule'
        verbose_name_plural = 'Employee Schedules'
        ordering            = ['-effective_from']

    def __str__(self):
        return f'{self.employee.full_name} — {self.schedule.name}'


class AttendanceLog(models.Model):
    class Source(models.TextChoices):
        FINGER_MACHINE = 'FINGER', 'Mesin Finger'
        MANUAL         = 'MANUAL', 'Manual (HR)'
        SYSTEM         = 'SYSTEM', 'System'

    employee      = models.ForeignKey(
        'employees.Employee',
        on_delete=models.PROTECT,
        related_name='attendance_logs',
        verbose_name='Karyawan',
    )
    date          = models.DateField(verbose_name='Tanggal')
    check_in      = models.TimeField(null=True, blank=True, verbose_name='Jam Masuk')
    check_out     = models.TimeField(null=True, blank=True, verbose_name='Jam Keluar')
    source        = models.CharField(
        max_length=6,
        choices=Source.choices,
        default=Source.FINGER_MACHINE,
        verbose_name='Sumber Data',
    )
    late_minutes  = models.PositiveSmallIntegerField(default=0, verbose_name='Keterlambatan (menit)')
    early_minutes = models.PositiveSmallIntegerField(default=0, verbose_name='Pulang Awal (menit)')
    work_minutes  = models.PositiveSmallIntegerField(default=0, verbose_name='Durasi Kerja (menit)')
    notes         = models.TextField(blank=True, verbose_name='Catatan')
    raw_data      = models.JSONField(
        null=True, blank=True,
        verbose_name='Raw Data',
        help_text='Data mentah dari mesin finger / sumber eksternal',
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Attendance Log'
        verbose_name_plural = 'Attendance Logs'
        unique_together     = [('employee', 'date')]
        ordering            = ['-date', 'employee']

    def __str__(self):
        return f'{self.employee.full_name} — {self.date}'
