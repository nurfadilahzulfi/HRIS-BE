from django.db import models


class SalaryComponent(models.Model):
    class ComponentType(models.TextChoices):
        EARNING   = 'EARNING',   'Penghasilan'
        DEDUCTION = 'DEDUCTION', 'Potongan'

    class FormulaType(models.TextChoices):
        FIXED                = 'FIXED',      'Nominal Tetap'
        PERCENTAGE_OF_BASIC  = 'PCT_BASIC',  '% dari Gaji Pokok'
        CUSTOM               = 'CUSTOM',     'Formula Kustom'

    entity         = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='salary_components', verbose_name='Entitas',
    )
    name           = models.CharField(max_length=100, verbose_name='Nama Komponen')
    component_type = models.CharField(max_length=9, choices=ComponentType.choices, verbose_name='Tipe')
    is_taxable     = models.BooleanField(default=True, verbose_name='Kena Pajak')
    is_fixed       = models.BooleanField(default=True, verbose_name='Tetap (bukan variabel)')
    formula_type   = models.CharField(
        max_length=9, choices=FormulaType.choices,
        default=FormulaType.FIXED, verbose_name='Tipe Formula',
    )
    formula_value  = models.DecimalField(
        max_digits=10, decimal_places=4, default=0,
        verbose_name='Nilai Formula',
        help_text='Nominal (FIXED) atau persentase (PCT_BASIC, mis. 10 = 10%)',
    )
    is_active      = models.BooleanField(default=True, verbose_name='Aktif')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Salary Component'
        verbose_name_plural = 'Salary Components'
        unique_together     = [('entity', 'name')]
        ordering            = ['component_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.component_type})'


class EmployeeSalaryComponent(models.Model):
    employee  = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='salary_components', verbose_name='Karyawan',
    )
    component = models.ForeignKey(
        SalaryComponent, on_delete=models.CASCADE,
        related_name='employee_assignments', verbose_name='Komponen',
    )
    amount    = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Nominal',
        help_text='Override nominal komponen untuk karyawan ini',
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    effective_from = models.DateField(null=True, blank=True, verbose_name='Berlaku Mulai')

    class Meta:
        verbose_name        = 'Employee Salary Component'
        verbose_name_plural = 'Employee Salary Components'
        unique_together     = [('employee', 'component')]

    def __str__(self):
        return f'{self.employee.full_name} — {self.component.name}: {self.amount}'


class OvertimeRecord(models.Model):
    class OvertimeType(models.TextChoices):
        WEEKDAY = 'WEEKDAY', 'Hari Kerja'
        WEEKEND = 'WEEKEND', 'Hari Libur/Akhir Pekan'
        HOLIDAY = 'HOLIDAY', 'Hari Nasional'

    employee        = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='overtime_records', verbose_name='Karyawan',
    )
    date            = models.DateField(verbose_name='Tanggal Lembur')
    hours_worked    = models.DecimalField(
        max_digits=4, decimal_places=1, verbose_name='Jam Lembur',
    )
    overtime_type   = models.CharField(
        max_length=7, choices=OvertimeType.choices,
        default=OvertimeType.WEEKDAY, verbose_name='Tipe Lembur',
    )
    rate_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.5,
        verbose_name='Multiplier Tarif',
    )
    amount          = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Nominal Lembur (calculated)',
    )
    payroll_period  = models.ForeignKey(
        'PayrollPeriod', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='overtime_records', verbose_name='Periode Payroll',
    )
    notes           = models.TextField(blank=True, verbose_name='Catatan')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Overtime Record'
        verbose_name_plural = 'Overtime Records'
        ordering            = ['-date']

    def __str__(self):
        return f'{self.employee.full_name} — {self.date} ({self.hours_worked} jam)'

    def calculate_amount(self, monthly_salary: float) -> float:
        """
        Hitung lembur sesuai aturan Ketenagakerjaan Indonesia:
        Tarif per jam = (1/173) × gaji sebulan
        Hari kerja biasa : jam ke-1 = 1.5×, jam ke-2+ = 2×
        Hari libur/nasional: jam ke-1 s/d 8 = 2×, jam ke-9 = 3×, jam ke-10+ = 4×
        """
        hourly_rate = monthly_salary / 173
        hours = float(self.hours_worked)

        if self.overtime_type == self.OvertimeType.WEEKDAY:
            if hours <= 1:
                total = hourly_rate * 1.5 * hours
            else:
                total = (hourly_rate * 1.5) + (hourly_rate * 2 * (hours - 1))
        else:  # WEEKEND / HOLIDAY
            if hours <= 8:
                total = hourly_rate * 2 * hours
            elif hours == 9:
                total = (hourly_rate * 2 * 8) + (hourly_rate * 3)
            else:
                total = (hourly_rate * 2 * 8) + (hourly_rate * 3) + (hourly_rate * 4 * (hours - 9))

        return round(total, 2)


class PayrollPeriod(models.Model):
    class Status(models.TextChoices):
        DRAFT      = 'DRAFT',      'Draft'
        PROCESSING = 'PROCESSING', 'Sedang Diproses'
        FINALIZED  = 'FINALIZED',  'Final'
        PAID       = 'PAID',       'Sudah Dibayar'

    entity       = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='payroll_periods', verbose_name='Entitas',
    )
    month        = models.PositiveSmallIntegerField(verbose_name='Bulan')
    year         = models.PositiveSmallIntegerField(verbose_name='Tahun')
    status       = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.DRAFT, verbose_name='Status',
    )
    finalized_at = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Finalisasi')
    created_by   = models.ForeignKey(
        'core.User', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_payroll_periods', verbose_name='Dibuat Oleh',
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Payroll Period'
        verbose_name_plural = 'Payroll Periods'
        unique_together     = [('entity', 'month', 'year')]
        ordering            = ['-year', '-month']

    def __str__(self):
        return f'{self.entity.code} — {self.month:02d}/{self.year} ({self.status})'


class PayrollItem(models.Model):
    class PPh21Scheme(models.TextChoices):
        GROSS     = 'GROSS',    'Gross (dipotong dari gaji)'
        GROSS_UP  = 'GROSS_UP', 'Gross Up (ditanggung perusahaan)'
        NET       = 'NET',      'Net (tidak direfleksikan)'

    period           = models.ForeignKey(
        PayrollPeriod, on_delete=models.CASCADE,
        related_name='items', verbose_name='Periode',
    )
    employee         = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='payroll_items', verbose_name='Karyawan',
    )
    pph21_scheme     = models.CharField(
        max_length=8, choices=PPh21Scheme.choices,
        default=PPh21Scheme.GROSS, verbose_name='Skema PPh21',
    )

    # ── Penghasilan ──────────────────────────────────────────────
    basic_salary      = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_allowances  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_overtime    = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gross_salary      = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # ── BPJS ─────────────────────────────────────────────────────
    bpjs_kes_employee  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_kes_employer  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jkk_employer  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jkm_employer  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jht_employee  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jht_employer  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jp_employee   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bpjs_jp_employer   = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Pajak ────────────────────────────────────────────────────
    pph21_amount       = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Total ────────────────────────────────────────────────────
    total_deductions   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_salary         = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # ── Detail JSON ──────────────────────────────────────────────
    breakdown          = models.JSONField(
        default=dict,
        verbose_name='Breakdown Komponen',
        help_text='Detail lengkap semua komponen gaji',
    )

    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Payroll Item'
        verbose_name_plural = 'Payroll Items'
        unique_together     = [('period', 'employee')]

    def __str__(self):
        return f'{self.employee.full_name} — {self.period}'
