from django.db import models


class KPITemplate(models.Model):
    class PeriodType(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Bulanan'
        QUARTERLY = 'QUARTERLY', 'Triwulan (3 Bulan)'
        ANNUAL = 'ANNUAL', 'Tahunan'

    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='kpi_templates', verbose_name='Entitas'
    )
    title = models.CharField(max_length=255, verbose_name='Judul Template KPI')
    department = models.ForeignKey(
        'employees.Department', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='kpi_templates',
        verbose_name='Departemen'
    )
    period_type = models.CharField(
        max_length=10, choices=PeriodType.choices,
        default=PeriodType.MONTHLY, verbose_name='Tipe Periode'
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'KPI Template'
        verbose_name_plural = 'KPI Templates'

    def __str__(self):
        return f'{self.title} ({self.entity.code})'


class KPIItem(models.Model):
    template = models.ForeignKey(
        KPITemplate, on_delete=models.CASCADE,
        related_name='items', verbose_name='Template KPI'
    )
    indicator = models.CharField(max_length=255, verbose_name='Indikator Kinerja')
    target = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Target')
    unit = models.CharField(max_length=50, verbose_name='Satuan (misal: %, Transaksi, Jam)')
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Bobot (%)',
        help_text='Total bobot dalam 1 template idealnya 100%'
    )

    class Meta:
        verbose_name = 'KPI Item'
        verbose_name_plural = 'KPI Items'

    def __str__(self):
        return f'{self.indicator} (Target: {self.target} {self.unit})'


class EmployeeKPIAssignment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Diajukan'
        APPROVED = 'APPROVED', 'Disetujui Manager'
        FINAL = 'FINAL', 'Final (Evaluasi Selesai)'

    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='kpi_assignments', verbose_name='Karyawan'
    )
    template = models.ForeignKey(
        KPITemplate, on_delete=models.CASCADE,
        related_name='assignments', verbose_name='Template KPI'
    )
    period_year = models.PositiveSmallIntegerField(verbose_name='Tahun Periode')
    period_index = models.PositiveSmallIntegerField(
        default=1, verbose_name='Indeks Periode',
        help_text='Bulan (1-12) atau Triwulan (1-4) atau 1 (Tahunan)'
    )
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.DRAFT, verbose_name='Status'
    )
    final_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Nilai KPI Akhir (%)'
    )
    evaluator_notes = models.TextField(blank=True, verbose_name='Catatan Evaluator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employee KPI Assignment'
        verbose_name_plural = 'Employee KPI Assignments'
        unique_together = [('employee', 'template', 'period_year', 'period_index')]

    def __str__(self):
        return f'{self.employee.full_name} — {self.template.title} ({self.period_year}-{self.period_index})'


class EmployeeKPIResultItem(models.Model):
    assignment = models.ForeignKey(
        EmployeeKPIAssignment, on_delete=models.CASCADE,
        related_name='results', verbose_name='Penugasan KPI'
    )
    kpi_item = models.ForeignKey(
        KPIItem, on_delete=models.CASCADE,
        verbose_name='Indikator KPI'
    )
    actual_achievement = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Capaian Aktual'
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Skor Terbobot (%)'
    )

    class Meta:
        verbose_name = 'Employee KPI Result Item'
        verbose_name_plural = 'Employee KPI Result Items'

    def __str__(self):
        return f'{self.kpi_item.indicator}: {self.actual_achievement}/{self.kpi_item.target}'
