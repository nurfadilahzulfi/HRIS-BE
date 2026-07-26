import io
from django.core.files.base import ContentFile
from django.utils import timezone
from django.template.loader import render_to_string
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .models import SalarySlip, SignatureConfig


def generate_slip_pdf(payroll_item) -> SalarySlip:
    """
    Generate PDF slip gaji dari PayrollItem.
    Flow:
    1. Render HTML template → WeasyPrint → PDF bytes
    2. (Opsional) Embed tanda tangan digital
    3. Simpan PDF ke storage
    4. Update SalarySlip record
    """
    employee = payroll_item.employee
    period   = payroll_item.period
    entity   = period.entity

    # Tentukan nomor slip
    seq = SalarySlip.objects.filter(
        payroll_item__period=period
    ).count() + 1

    slip_number = SalarySlip.generate_slip_number(
        entity.code, period.year, period.month, seq
    )

    # Upsert SalarySlip
    slip, _ = SalarySlip.objects.get_or_create(
        payroll_item=payroll_item,
        defaults={'slip_number': slip_number},
    )

    if not WEASYPRINT_AVAILABLE:
        # WeasyPrint tidak tersedia — simpan placeholder
        slip.generated_at = timezone.now()
        slip.save(update_fields=['generated_at'])
        return slip

    # Render HTML
    try:
        sig_config = entity.signature_config
    except SignatureConfig.DoesNotExist:
        sig_config = None

    html_content = render_to_string('salary_slip/slip_template.html', {
        'slip':          slip,
        'payroll_item':  payroll_item,
        'employee':      employee,
        'entity':        entity,
        'period':        period,
        'breakdown':     payroll_item.breakdown,
        'sig_config':    sig_config,
    })

    # PDF generation
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

    # Simpan PDF
    filename = f'{slip_number}.pdf'
    slip.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
    slip.is_signed    = sig_config is not None
    slip.generated_at = timezone.now()
    slip.save(update_fields=['pdf_file', 'is_signed', 'generated_at'])

    return slip
