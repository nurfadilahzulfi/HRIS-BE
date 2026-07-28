import io
from django.core.files.base import ContentFile
from django.utils import timezone
from django.template.loader import render_to_string
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .models import SalarySlip, SignatureConfig


def _embed_signature_to_pdf(pdf_bytes: bytes, sig_config: SignatureConfig) -> bytes:
    """
    Embed tanda tangan digital ke PDF menggunakan Pillow.
    Karena WeasyPrint menghasilkan PDF murni, TTD di-embed via HTML rendering
    (image sudah dirender langsung di template). Fungsi ini reserved untuk
    kebutuhan overlay lanjutan jika menggunakan pikranti PDF-manipulasi seperti
    pikepdf atau pypdf. Untuk sekarang, WeasyPrint render TTD via HTML.
    """
    # Signature sudah dirender langsung di HTML template melalui src path.
    # Fungsi ini bisa digunakan di masa depan untuk overlay langsung ke PDF byte stream.
    return pdf_bytes


def generate_signature_watermark(sig_config: SignatureConfig, width: int = 400, height: int = 150) -> bytes:
    """
    Generate gambar watermark tanda tangan menggunakan Pillow.
    Returns PNG bytes yang bisa digunakan sebagai overlay.
    """
    if not PILLOW_AVAILABLE or not sig_config or not sig_config.signature_image:
        return None

    try:
        # Buka gambar TTD original
        sig_path = sig_config.signature_image.path
        img = Image.open(sig_path).convert('RGBA')

        # Resize ke ukuran yang sesuai
        img.thumbnail((width, height), Image.LANCZOS)

        # Buat canvas transparan
        canvas = Image.new('RGBA', (width, height), (255, 255, 255, 0))

        # Paste gambar TTD ke tengah canvas
        x = (width - img.width) // 2
        y = (height - img.height) // 2
        canvas.paste(img, (x, y), mask=img)

        # Convert ke bytes
        buffer = io.BytesIO()
        canvas.save(buffer, format='PNG')
        return buffer.getvalue()
    except Exception:
        return None


def generate_slip_pdf(payroll_item) -> SalarySlip:
    """
    Generate PDF slip gaji dari PayrollItem.

    Flow:
    1. Render HTML template → WeasyPrint → PDF bytes
    2. Tanda tangan digital di-embed via img tag di HTML template (Pillow-verified)
    3. Simpan PDF ke storage
    4. Update SalarySlip record
    """
    employee = payroll_item.employee
    period   = payroll_item.period
    entity   = period.entity

    # ── Tentukan nomor slip (sequential per period) ───────────────────
    seq = SalarySlip.objects.filter(
        payroll_item__period=period
    ).count() + 1

    slip_number = SalarySlip.generate_slip_number(
        entity.code, period.year, period.month, seq
    )

    # ── Upsert SalarySlip record ──────────────────────────────────────
    slip, created = SalarySlip.objects.get_or_create(
        payroll_item=payroll_item,
        defaults={'slip_number': slip_number},
    )

    if not WEASYPRINT_AVAILABLE:
        # WeasyPrint tidak tersedia — catat sebagai generated tanpa PDF
        slip.generated_at = timezone.now()
        slip.save(update_fields=['generated_at'])
        return slip

    # ── Ambil konfigurasi tanda tangan ────────────────────────────────
    try:
        sig_config = entity.signature_config
    except SignatureConfig.DoesNotExist:
        sig_config = None

    # ── Verifikasi tanda tangan dengan Pillow (jika tersedia) ─────────
    has_valid_signature = False
    if sig_config and sig_config.signature_image and PILLOW_AVAILABLE:
        try:
            # Validasi bahwa gambar TTD bisa dibuka dan tidak corrupt
            sig_img = Image.open(sig_config.signature_image.path)
            sig_img.verify()
            has_valid_signature = True
        except Exception:
            has_valid_signature = False
    elif sig_config and sig_config.signature_image:
        has_valid_signature = True  # Pillow tidak tersedia, asumsikan valid

    # ── Render HTML template ──────────────────────────────────────────
    html_content = render_to_string('salary_slip/slip_template.html', {
        'slip':         slip,
        'payroll_item': payroll_item,
        'employee':     employee,
        'entity':       entity,
        'period':       period,
        'breakdown':    payroll_item.breakdown,
        'sig_config':   sig_config if has_valid_signature else None,
    })

    # ── Generate PDF via WeasyPrint ───────────────────────────────────
    pdf_bytes = weasyprint.HTML(
        string=html_content,
        base_url=None,
    ).write_pdf()

    # ── Simpan PDF ke storage ─────────────────────────────────────────
    filename = f'{slip.slip_number}.pdf'
    slip.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
    slip.is_signed    = has_valid_signature
    slip.generated_at = timezone.now()
    slip.save(update_fields=['pdf_file', 'is_signed', 'generated_at'])

    return slip
