"""
PPh21 Engine — sesuai UU HPP 2021
Mendukung 3 skema: GROSS, GROSS_UP, NET
"""
from decimal import Decimal
from .models import PTKP, PPh21Bracket


# Biaya jabatan: 5% dari bruto, max Rp 500.000/bulan = Rp 6.000.000/tahun
BIAYA_JABATAN_RATE  = Decimal('0.05')
BIAYA_JABATAN_MAX_MONTHLY = Decimal('500000')
BIAYA_JABATAN_MAX_ANNUAL  = Decimal('6000000')


def get_ptkp(year: int, status_code: str) -> Decimal:
    try:
        return PTKP.objects.get(year=year, status_code=status_code).amount
    except PTKP.DoesNotExist:
        # Fallback ke PTKP 2024 standar TK/0
        return Decimal('54000000')


def calculate_progressive_tax(pkp_annual: Decimal, year: int) -> Decimal:
    """Hitung PPh21 progresif dari PKP tahunan."""
    brackets = PPh21Bracket.objects.filter(year=year).order_by('income_from')
    if not brackets.exists():
        # Default brackets UU HPP 2021
        default_brackets = [
            (Decimal('0'),          Decimal('60000000'),   Decimal('0.05')),
            (Decimal('60000000'),   Decimal('250000000'),  Decimal('0.15')),
            (Decimal('250000000'),  Decimal('500000000'),  Decimal('0.25')),
            (Decimal('500000000'),  Decimal('5000000000'), Decimal('0.30')),
            (Decimal('5000000000'), None,                  Decimal('0.35')),
        ]
        tax = Decimal('0')
        for from_amt, to_amt, rate in default_brackets:
            if pkp_annual <= from_amt:
                break
            taxable = (min(pkp_annual, to_amt) if to_amt else pkp_annual) - from_amt
            tax += taxable * rate
        return tax

    tax = Decimal('0')
    for bracket in brackets:
        if pkp_annual <= bracket.income_from:
            break
        upper  = bracket.income_to if bracket.income_to else pkp_annual
        taxable = min(pkp_annual, upper) - bracket.income_from
        if taxable > 0:
            tax += taxable * (bracket.rate / 100)
    return tax


def calculate_pph21(
    gross_monthly: Decimal,
    ptkp_status: str,
    scheme: str,
    year: int,
    bpjs_employee_monthly: Decimal = Decimal('0'),
) -> dict:
    """
    Hitung PPh21 bulanan dengan 3 skema.

    Returns dict dengan semua step perhitungan (audit trail).
    """
    gross_annual  = gross_monthly * 12
    bpjs_annual   = bpjs_employee_monthly * 12

    # Biaya jabatan
    biaya_jabatan_monthly = min(gross_monthly * BIAYA_JABATAN_RATE, BIAYA_JABATAN_MAX_MONTHLY)
    biaya_jabatan_annual  = min(biaya_jabatan_monthly * 12, BIAYA_JABATAN_MAX_ANNUAL)

    # Penghasilan neto sebelum PTKP
    net_annual = gross_annual - biaya_jabatan_annual - bpjs_annual

    ptkp_amount = get_ptkp(year, ptkp_status)

    # PKP
    pkp_annual = max(net_annual - ptkp_amount, Decimal('0'))
    # Pembulatan ke bawah ribuan
    pkp_annual = (pkp_annual // 1000) * 1000

    tax_annual  = calculate_progressive_tax(pkp_annual, year)
    tax_monthly = (tax_annual / 12).quantize(Decimal('1'))

    detail = {
        'gross_monthly':        float(gross_monthly),
        'gross_annual':         float(gross_annual),
        'biaya_jabatan_monthly': float(biaya_jabatan_monthly),
        'biaya_jabatan_annual': float(biaya_jabatan_annual),
        'bpjs_employee_annual': float(bpjs_annual),
        'net_annual':           float(net_annual),
        'ptkp_status':          ptkp_status,
        'ptkp_amount':          float(ptkp_amount),
        'pkp_annual':           float(pkp_annual),
        'tax_annual':           float(tax_annual),
        'tax_monthly':          float(tax_monthly),
        'scheme':               scheme,
    }

    if scheme == 'GROSS':
        # Dipotong dari gaji karyawan — langsung
        detail['employee_burden'] = float(tax_monthly)
        detail['employer_burden'] = 0

    elif scheme == 'GROSS_UP':
        # Perusahaan menanggung → PPh21 menjadi tunjangan tambahan
        # Hitung gross-up: cari bruto setelah tunjangan PPh = bruto + PPh
        # Iterasi untuk gross-up (karena PPh bertingkat)
        grossed_up_monthly = gross_monthly + tax_monthly
        for _ in range(5):   # converge dalam ~5 iterasi
            g_annual = grossed_up_monthly * 12
            bj_annual = min(grossed_up_monthly * BIAYA_JABATAN_RATE * 12, BIAYA_JABATAN_MAX_ANNUAL)
            net_a = g_annual - bj_annual - bpjs_annual
            pkp_a = max((net_a - ptkp_amount) // 1000 * 1000, Decimal('0'))
            tax_a = calculate_progressive_tax(pkp_a, year)
            tax_m = (tax_a / 12).quantize(Decimal('1'))
            grossed_up_monthly = gross_monthly + tax_m
            tax_monthly = tax_m

        detail['tunjangan_pph21']  = float(tax_monthly)
        detail['employee_burden']  = 0
        detail['employer_burden']  = float(tax_monthly)

    else:  # NET
        # Perusahaan menanggung tapi tidak direfleksikan di slip
        detail['employee_burden']  = 0
        detail['employer_burden']  = float(tax_monthly)
        tax_monthly = Decimal('0')  # tidak dipotong dari gaji karyawan

    return {
        'tax_monthly':    tax_monthly,
        'ptkp_amount':    ptkp_amount,
        'pkp_annual':     pkp_annual,
        'tax_annual':     tax_annual,
        'biaya_jabatan':  biaya_jabatan_annual,
        'detail':         detail,
    }
