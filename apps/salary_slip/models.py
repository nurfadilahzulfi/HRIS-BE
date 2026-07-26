from django.db import models


class SignatureConfig(models.Model):
    entity           = models.OneToOneField(
        'company.Entity', on_delete=models.CASCADE,
        related_name='signature_config', verbose_name='Entitas',
    )
    signer_name      = models.CharField(max_length=100, verbose_name='Nama Penandatangan')
    signer_position  = models.CharField(max_length=100, verbose_name='Jabatan Penandatangan')
    signature_image  = models.ImageField(
        upload_to='salary_slip/signatures/',
        verbose_name='Gambar Tanda Tangan',
    )
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Signature Config'
        verbose_name_plural = 'Signature Configs'

    def __str__(self):
        return f'TTD Config: {self.entity.code} — {self.signer_name}'


class SalarySlip(models.Model):
    payroll_item = models.OneToOneField(
        'payroll.PayrollItem', on_delete=models.CASCADE,
        related_name='salary_slip', verbose_name='Payroll Item',
    )
    slip_number  = models.CharField(
        max_length=50, unique=True,
        verbose_name='Nomor Slip',
        help_text='Format: SLIP-HO-2024-06-0001',
    )
    pdf_file     = models.FileField(
        upload_to='salary_slip/pdfs/',
        null=True, blank=True,
        verbose_name='File PDF',
    )
    is_signed    = models.BooleanField(default=False, verbose_name='Sudah Ditandatangani')
    generated_at = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Generate')
    is_sent      = models.BooleanField(default=False, verbose_name='Sudah Dikirim')
    sent_at      = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Dikirim')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Salary Slip'
        verbose_name_plural = 'Salary Slips'
        ordering            = ['-created_at']

    def __str__(self):
        return self.slip_number

    @classmethod
    def generate_slip_number(cls, entity_code: str, year: int, month: int, sequence: int) -> str:
        return f'SLIP-{entity_code}-{year}-{month:02d}-{str(sequence).zfill(4)}'
