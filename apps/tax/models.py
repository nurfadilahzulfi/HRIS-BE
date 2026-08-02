from django.db import models


class PTKP(models.Model):
    """PTKP table — update per tahun pajak."""
    year        = models.PositiveSmallIntegerField(verbose_name='Tahun Pajak')
    status_code = models.CharField(
        max_length=5, verbose_name='Kode Status PTKP',
        help_text='TK/0, TK/1, K/0, K/1, K/2, K/3',
    )
    amount      = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Nilai PTKP')

    class Meta:
        verbose_name        = 'PTKP'
        verbose_name_plural = 'PTKP'
        unique_together     = [('year', 'status_code')]
        ordering            = ['year', 'status_code']

    def __str__(self):
        return f'{self.status_code} ({self.year}): Rp {self.amount:,.0f}'


class PPh21Bracket(models.Model):
    """Tarif PPh21 progresif sesuai UU HPP 2021."""
    year        = models.PositiveSmallIntegerField(verbose_name='Tahun Pajak')
    income_from = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='PKP Dari (Rp)')
    income_to   = models.DecimalField(
        max_digits=20, decimal_places=2,
        null=True, blank=True,
        verbose_name='PKP Sampai (Rp)',
        help_text='Kosongkan untuk bracket terakhir (> X)',
    )
    rate        = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Tarif (%)',
    )

    class Meta:
        verbose_name        = 'PPh21 Bracket'
        verbose_name_plural = 'PPh21 Brackets'
        unique_together     = [('year', 'income_from')]
        ordering            = ['year', 'income_from']

    def __str__(self):
        return f'{self.year}: {self.income_from:,.0f}–{self.income_to or "∞"} → {self.rate}%'


class PPh21TERRate(models.Model):
    """
    Tabel TER (Tarif Efektif Rata-rata) sesuai PMK 168/2023, dipakai untuk
    pemotongan bulanan Januari-November. Bulan Desember memakai PPh21Bracket
    (Pasal 17) untuk rekonsiliasi tahunan.
    """
    class Category(models.TextChoices):
        A = 'A', 'Kategori A'
        B = 'B', 'Kategori B'
        C = 'C', 'Kategori C'

    year         = models.PositiveSmallIntegerField(verbose_name='Tahun Pajak')
    category     = models.CharField(max_length=1, choices=Category.choices, verbose_name='Kategori TER')
    income_from  = models.DecimalField(max_digits=20, decimal_places=2, verbose_name='Bruto Dari (Rp)')
    income_to    = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        verbose_name='Bruto Sampai (Rp)', help_text='Kosongkan untuk bracket tertinggi',
    )
    rate_percent = models.DecimalField(max_digits=5, decimal_places=3, verbose_name='Tarif (%)')

    class Meta:
        verbose_name        = 'PPh21 TER Rate'
        verbose_name_plural = 'PPh21 TER Rates'
        unique_together     = [('year', 'category', 'income_from')]
        ordering            = ['year', 'category', 'income_from']

    def __str__(self):
        return f'{self.year} Kat {self.category}: {self.income_from:,.0f}–{self.income_to or "∞"} → {self.rate_percent}%'


class TaxCalculationLog(models.Model):
    """Audit trail kalkulasi PPh21 per payroll item."""
    payroll_item   = models.OneToOneField(
        'payroll.PayrollItem', on_delete=models.PROTECT,
        related_name='tax_log', verbose_name='Payroll Item',
    )
    scheme         = models.CharField(max_length=8, verbose_name='Skema PPh21')
    ptkp_status    = models.CharField(max_length=5, verbose_name='Status PTKP')
    ptkp_amount    = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Nilai PTKP')
    gross_annual   = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Penghasilan Bruto Setahun')
    biaya_jabatan  = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Biaya Jabatan')
    pkp_annual     = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='PKP Setahun')
    tax_annual     = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='PPh21 Setahun')
    tax_monthly    = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='PPh21 per Bulan')
    detail         = models.JSONField(default=dict, verbose_name='Detail Perhitungan')
    calculated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Tax Calculation Log'
        verbose_name_plural = 'Tax Calculation Logs'

    def __str__(self):
        return f'Tax Log: {self.payroll_item} — {self.scheme}'
