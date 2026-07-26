"""
BPJS Calculator — sesuai regulasi standar Indonesia
"""
from decimal import Decimal


# ── BPJS Kesehatan ──────────────────────────────────────────────────────────
BPJS_KES_EMPLOYER_RATE = Decimal('0.04')   # 4%
BPJS_KES_EMPLOYEE_RATE = Decimal('0.01')   # 1%
BPJS_KES_CAP           = Decimal('12000000')  # cap gaji untuk BPJS Kes

# ── BPJS Ketenagakerjaan ────────────────────────────────────────────────────
JKK_RATE   = Decimal('0.0024')   # 0.24% (risiko rendah; range 0.24–1.74%)
JKM_RATE   = Decimal('0.003')    # 0.30%
JHT_EMPLOYER_RATE = Decimal('0.037')  # 3.70%
JHT_EMPLOYEE_RATE = Decimal('0.02')   # 2%
JP_EMPLOYER_RATE  = Decimal('0.02')   # 2%
JP_EMPLOYEE_RATE  = Decimal('0.01')   # 1%
JP_CAP             = Decimal('9559600')  # cap gaji untuk JP (update berkala)


def calculate_bpjs(basic_salary: Decimal, total_fixed_allowances: Decimal = Decimal('0')) -> dict:
    """
    Hitung seluruh komponen BPJS.

    Args:
        basic_salary: Gaji pokok
        total_fixed_allowances: Total tunjangan tetap (untuk dasar BPJS Kes)

    Returns dict berisi semua komponen employee & employer.
    """
    # Dasar BPJS Kesehatan = gaji pokok + tunjangan tetap, max 12 juta
    bpjs_kes_base = min(basic_salary + total_fixed_allowances, BPJS_KES_CAP)
    bpjs_kes_employee = (bpjs_kes_base * BPJS_KES_EMPLOYEE_RATE).quantize(Decimal('1'))
    bpjs_kes_employer = (bpjs_kes_base * BPJS_KES_EMPLOYER_RATE).quantize(Decimal('1'))

    # Dasar JKK, JKM, JHT = upah (gaji pokok + tunjangan tetap)
    upah = basic_salary + total_fixed_allowances

    jkk = (upah * JKK_RATE).quantize(Decimal('1'))
    jkm = (upah * JKM_RATE).quantize(Decimal('1'))

    jht_employee = (upah * JHT_EMPLOYEE_RATE).quantize(Decimal('1'))
    jht_employer = (upah * JHT_EMPLOYER_RATE).quantize(Decimal('1'))

    # Dasar JP = min(upah, JP_CAP)
    jp_base = min(upah, JP_CAP)
    jp_employee = (jp_base * JP_EMPLOYEE_RATE).quantize(Decimal('1'))
    jp_employer = (jp_base * JP_EMPLOYER_RATE).quantize(Decimal('1'))

    total_employee = bpjs_kes_employee + jht_employee + jp_employee
    total_employer = bpjs_kes_employer + jkk + jkm + jht_employer + jp_employer

    return {
        # BPJS Kesehatan
        'bpjs_kes_base':     float(bpjs_kes_base),
        'bpjs_kes_employee': float(bpjs_kes_employee),
        'bpjs_kes_employer': float(bpjs_kes_employer),
        # JKK & JKM (employer only)
        'bpjs_jkk_employer': float(jkk),
        'bpjs_jkm_employer': float(jkm),
        # JHT
        'bpjs_jht_employee': float(jht_employee),
        'bpjs_jht_employer': float(jht_employer),
        # JP
        'bpjs_jp_employee':  float(jp_employee),
        'bpjs_jp_employer':  float(jp_employer),
        # Totals
        'total_employee_bpjs': float(total_employee),
        'total_employer_bpjs': float(total_employer),
    }
