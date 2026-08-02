from django.db import models


class Contract(models.Model):
    class ContractType(models.TextChoices):
        PKWT  = 'PKWT',  'PKWT (Karyawan Kontrak)'
        PKWTT = 'PKWTT', 'PKWTT (Karyawan Tetap)'
        BHL   = 'BHL',   'BHL (Buruh Harian Lepas)'

    class Status(models.TextChoices):
        ACTIVE     = 'ACTIVE',     'Aktif'
        EXPIRED    = 'EXPIRED',    'Expired'
        TERMINATED = 'TERMINATED', 'Diakhiri'
        RENEWED    = 'RENEWED',    'Diperbarui'

    employee      = models.ForeignKey(
        'employees.Employee',
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name='Karyawan',
    )
    contract_type = models.CharField(
        max_length=5,
        choices=ContractType.choices,
        verbose_name='Jenis Kontrak',
    )
    start_date    = models.DateField(verbose_name='Tanggal Mulai')
    end_date      = models.DateField(
        null=True, blank=True,
        verbose_name='Tanggal Selesai',
        help_text='Kosongkan untuk PKWTT (karyawan tetap)',
    )
    salary_base   = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Gaji Pokok',
    )
    document      = models.FileField(
        upload_to='contracts/documents/',
        null=True, blank=True,
        verbose_name='Dokumen Kontrak (PDF)',
    )
    status        = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Status',
    )
    notes         = models.TextField(blank=True, verbose_name='Catatan')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Contract'
        verbose_name_plural = 'Contracts'
        ordering            = ['-start_date']

    def __str__(self):
        return f'{self.employee.full_name} — {self.contract_type} ({self.status})'

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE

    @property
    def days_until_expiry(self):
        if not self.end_date:
            return None
        from django.utils import timezone
        delta = self.end_date - timezone.now().date()
        return delta.days

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.status == self.Status.ACTIVE and self.employee_id:
            conflicting = Contract.objects.filter(
                employee=self.employee, status=self.Status.ACTIVE
            ).exclude(pk=self.pk)
            if conflicting.exists():
                raise ValidationError(
                    "Karyawan ini sudah memiliki kontrak aktif lain. "
                    "Ubah status kontrak lama menjadi RENEWED/TERMINATED/EXPIRED terlebih dahulu."
                )

        if self.contract_type != self.ContractType.PKWTT and not self.end_date:
            raise ValidationError(
                f"Kontrak tipe {self.get_contract_type_display()} wajib memiliki tanggal berakhir."
            )

        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError("Tanggal berakhir tidak boleh lebih awal dari tanggal mulai.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ContractRenewal(models.Model):
    original_contract = models.ForeignKey(
        Contract,
        on_delete=models.PROTECT,
        related_name='renewals',
        verbose_name='Kontrak Asal',
    )
    new_end_date = models.DateField(verbose_name='Tanggal Berakhir Baru')
    new_salary_base = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        verbose_name='Gaji Pokok Baru',
        help_text='Kosongkan jika tidak ada perubahan gaji',
    )
    document     = models.FileField(
        upload_to='contracts/renewals/',
        null=True, blank=True,
        verbose_name='Dokumen Pembaruan',
    )
    notes        = models.TextField(blank=True, verbose_name='Catatan')
    renewed_by   = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='contract_renewals',
        verbose_name='Diperbarui Oleh',
    )
    renewed_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Contract Renewal'
        verbose_name_plural = 'Contract Renewals'
        ordering            = ['-renewed_at']

    def __str__(self):
        return f'Renewal: {self.original_contract} → {self.new_end_date}'
