from django.db import models


class LeaveType(models.Model):
    class ApplicableTo(models.TextChoices):
        PKWT  = 'PKWT',  'PKWT'
        PKWTT = 'PKWTT', 'PKWTT'
        ALL   = 'ALL',   'Semua (PKWT & PKWTT)'

    entity               = models.ForeignKey(
        'company.Entity',
        on_delete=models.CASCADE,
        related_name='leave_types',
        verbose_name='Entitas',
    )
    name                 = models.CharField(max_length=100, verbose_name='Nama Jenis Cuti')
    max_days_per_year    = models.PositiveSmallIntegerField(verbose_name='Maks. Hari per Tahun')
    is_paid              = models.BooleanField(default=True, verbose_name='Cuti Berbayar')
    applicable_to        = models.CharField(
        max_length=5,
        choices=ApplicableTo.choices,
        default=ApplicableTo.ALL,
        verbose_name='Berlaku untuk',
        help_text='BHL dikecualikan dari sistem cuti',
    )
    allow_halfday        = models.BooleanField(default=False, verbose_name='Boleh Setengah Hari')
    requires_attachment  = models.BooleanField(default=False, verbose_name='Wajib Lampiran')
    carry_forward_days   = models.PositiveSmallIntegerField(
        default=0, verbose_name='Maks. Carry Forward (hari)',
    )
    is_active            = models.BooleanField(default=True, verbose_name='Aktif')
    created_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Leave Type'
        verbose_name_plural = 'Leave Types'
        unique_together     = [('entity', 'name')]
        ordering            = ['name']

    def __str__(self):
        return f'{self.name} ({self.entity.code})'


class LeaveBalance(models.Model):
    employee    = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name='Karyawan',
    )
    leave_type  = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name='Jenis Cuti',
    )
    year        = models.PositiveSmallIntegerField(verbose_name='Tahun')
    allocated   = models.PositiveSmallIntegerField(default=0, verbose_name='Alokasi (hari)')
    used        = models.PositiveSmallIntegerField(default=0, verbose_name='Terpakai (hari)')
    carry_forward = models.PositiveSmallIntegerField(default=0, verbose_name='Carry Forward (hari)')

    class Meta:
        verbose_name        = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together     = [('employee', 'leave_type', 'year')]

    @property
    def remaining(self):
        return self.allocated + self.carry_forward - self.used

    def __str__(self):
        return f'{self.employee.full_name} — {self.leave_type.name} ({self.year}): {self.remaining} hari'


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'DRAFT',     'Draft'
        PENDING   = 'PENDING',   'Menunggu Persetujuan'
        APPROVED  = 'APPROVED',  'Disetujui'
        REJECTED  = 'REJECTED',  'Ditolak'
        CANCELLED = 'CANCELLED', 'Dibatalkan'

    employee    = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name='Karyawan',
    )
    leave_type  = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name='Jenis Cuti',
    )
    start_date  = models.DateField(verbose_name='Tanggal Mulai')
    end_date    = models.DateField(verbose_name='Tanggal Selesai')
    total_days  = models.DecimalField(
        max_digits=4, decimal_places=1,
        verbose_name='Jumlah Hari',
    )
    is_halfday  = models.BooleanField(default=False, verbose_name='Setengah Hari')
    reason      = models.TextField(verbose_name='Alasan Cuti')
    attachment  = models.FileField(
        upload_to='leave/attachments/',
        null=True, blank=True,
        verbose_name='Lampiran',
    )
    status      = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Status',
    )
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Pengajuan')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.employee.full_name} — {self.leave_type.name} ({self.start_date} s/d {self.end_date})'


class LeaveApproval(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Menunggu'
        APPROVED = 'APPROVED', 'Disetujui'
        REJECTED = 'REJECTED', 'Ditolak'

    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='Permohonan Cuti',
    )
    approver      = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_approvals',
        verbose_name='Approver',
    )
    level         = models.PositiveSmallIntegerField(
        verbose_name='Level Approval',
        help_text='1 = Direct Manager, 2 = Manager\'s Manager, dst.',
    )
    status        = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Status',
    )
    notes         = models.TextField(blank=True, verbose_name='Catatan Approver')
    acted_at      = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Keputusan')

    class Meta:
        verbose_name        = 'Leave Approval'
        verbose_name_plural = 'Leave Approvals'
        unique_together     = [('leave_request', 'level')]
        ordering            = ['level']

    def __str__(self):
        return f'Level {self.level}: {self.approver.full_name} — {self.status}'
