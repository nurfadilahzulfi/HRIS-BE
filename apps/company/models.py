from django.db import models


class Company(models.Model):
    name    = models.CharField(max_length=255, verbose_name='Nama Perusahaan')
    logo    = models.ImageField(upload_to='company/logos/', null=True, blank=True, verbose_name='Logo')
    address = models.TextField(verbose_name='Alamat')
    npwp    = models.CharField(max_length=30, blank=True, verbose_name='NPWP')
    phone   = models.CharField(max_length=20, blank=True, verbose_name='Telepon')
    email   = models.EmailField(blank=True, verbose_name='Email')
    website = models.URLField(blank=True, verbose_name='Website')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name


class Entity(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='entities',
        verbose_name='Perusahaan',
    )
    name    = models.CharField(max_length=255, verbose_name='Nama Entitas')
    code    = models.CharField(max_length=10, unique=True, verbose_name='Kode Entitas')
    address = models.TextField(blank=True, verbose_name='Alamat')
    npwp    = models.CharField(max_length=30, blank=True, verbose_name='NPWP')
    phone   = models.CharField(max_length=20, blank=True, verbose_name='Telepon')
    email   = models.EmailField(blank=True, verbose_name='Email')
    employee_id_last_sequence = models.PositiveIntegerField(default=0)

    # Payroll & Leave configuration per entity
    payroll_cutoff_day = models.PositiveSmallIntegerField(
        default=25,
        verbose_name='Tanggal Cutoff Payroll',
        help_text='Tanggal tutup buku penggajian setiap bulan (1-31)',
    )
    leave_approval_levels = models.PositiveSmallIntegerField(
        default=2,
        verbose_name='Jumlah Level Approval Cuti',
        help_text='Jumlah level approver untuk cuti (1 = direct manager only)',
    )

    # Employee ID format template
    # Available tokens: {ENTITY_CODE}, {YEAR}, {SEQ}
    # Default: HO-2024-0001
    employee_id_format = models.CharField(
        max_length=50,
        default='{ENTITY_CODE}-{YEAR}-{SEQ}',
        verbose_name='Format ID Karyawan',
    )
    employee_id_seq_padding = models.PositiveSmallIntegerField(
        default=4,
        verbose_name='Padding Nomor Urut',
        help_text='Jumlah digit untuk nomor urut (4 = 0001)',
    )

    is_active  = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entity'
        verbose_name_plural = 'Entities'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} — {self.name}'

    def generate_employee_id(self, year: int, sequence: int) -> str:
        """Generate employee ID based on entity's format template."""
        seq_str = str(sequence).zfill(self.employee_id_seq_padding)
        return (
            self.employee_id_format
            .replace('{ENTITY_CODE}', self.code)
            .replace('{YEAR}', str(year))
            .replace('{SEQ}', seq_str)
        )

    def next_employee_sequence(self) -> int:
        """
        Increment counter secara atomic dengan row lock, supaya aman
        dipanggil dari banyak request bersamaan tanpa race condition.
        WAJIB dipanggil di dalam transaction.atomic().
        """
        Entity.objects.filter(pk=self.pk).update(
            employee_id_last_sequence=models.F("employee_id_last_sequence") + 1
        )
        self.refresh_from_db(fields=["employee_id_last_sequence"])
        return self.employee_id_last_sequence
