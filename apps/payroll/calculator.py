"""
Payroll Calculator — orchestrates BPJS + PPh21 + components for a period.
"""
from decimal import Decimal
from django.utils import timezone

from .models import PayrollItem, OvertimeRecord, EmployeeSalaryComponent, SalaryComponent
from .bpjs import calculate_bpjs
from apps.tax.engine import calculate_pph21
from apps.tax.models import TaxCalculationLog


def calculate_payroll_item(period, employee) -> PayrollItem:
    """
    Hitung gaji satu karyawan untuk satu periode.
    Buat atau update PayrollItem.
    """
    year = period.year

    # 1. Gaji pokok dari kontrak aktif
    contract = employee.contracts.filter(status='ACTIVE').order_by('-start_date').first()
    basic_salary = Decimal(str(contract.salary_base)) if contract else Decimal('0')

    # 2. Komponen gaji
    emp_components = EmployeeSalaryComponent.objects.filter(
        employee=employee, is_active=True
    ).select_related('component')

    total_allowances = Decimal('0')
    total_deductions_components = Decimal('0')
    total_fixed_allowances = Decimal('0')
    component_details = []

    for ec in emp_components:
        comp = ec.component
        amount = ec.amount

        if comp.formula_type == 'PCT_BASIC':
            amount = (basic_salary * comp.formula_value / 100).quantize(Decimal('1'))
        elif comp.formula_type == 'FIXED':
            amount = ec.amount

        component_details.append({
            'name':   comp.name,
            'type':   comp.component_type,
            'amount': float(amount),
        })

        if comp.component_type == 'EARNING':
            total_allowances += amount
            if comp.is_fixed:
                total_fixed_allowances += amount
        else:
            total_deductions_components += amount

    # 3. Overtime bulan ini
    overtime_records = OvertimeRecord.objects.filter(
        employee=employee,
        date__month=period.month,
        date__year=period.year,
        payroll_period__isnull=True,
    )
    total_overtime = Decimal('0')
    for ot in overtime_records:
        ot_amount = Decimal(str(ot.calculate_amount(float(basic_salary))))
        ot.amount         = ot_amount
        ot.payroll_period = period
        ot.save(update_fields=['amount', 'payroll_period'])
        total_overtime += ot_amount

    # 4. Gross salary
    gross_salary = basic_salary + total_allowances + total_overtime

    # 5. BPJS
    bpjs = calculate_bpjs(basic_salary, total_fixed_allowances)
    bpjs_employee_total = Decimal(str(bpjs['total_employee_bpjs']))

    # 6. PPh21 — ambil scheme dari setting karyawan (configurable: GROSS/GROSS_UP/NET)
    pph21_scheme = getattr(employee, 'pph21_scheme', 'GROSS') or 'GROSS'
    pph21_result = calculate_pph21(
        gross_monthly=gross_salary,
        ptkp_status=employee.ptkp_status,
        scheme=pph21_scheme,
        year=year,
        bpjs_employee_monthly=bpjs_employee_total,
    )
    pph21_amount = pph21_result['tax_monthly']

    # 7. Total deductions & net
    total_deductions = bpjs_employee_total + pph21_amount + total_deductions_components
    net_salary       = gross_salary - total_deductions

    # 8. Build breakdown JSON
    breakdown = {
        'basic_salary':    float(basic_salary),
        'components':      component_details,
        'overtime':        float(total_overtime),
        'gross_salary':    float(gross_salary),
        'bpjs':            bpjs,
        'pph21':           pph21_result['detail'],
        'net_salary':      float(net_salary),
    }

    # 9. Upsert PayrollItem
    item, _ = PayrollItem.objects.update_or_create(
        period=period,
        employee=employee,
        defaults={
            'pph21_scheme':       pph21_scheme,
            'basic_salary':       basic_salary,
            'total_allowances':   total_allowances,
            'total_overtime':     total_overtime,
            'gross_salary':       gross_salary,
            'bpjs_kes_employee':  Decimal(str(bpjs['bpjs_kes_employee'])),
            'bpjs_kes_employer':  Decimal(str(bpjs['bpjs_kes_employer'])),
            'bpjs_jkk_employer':  Decimal(str(bpjs['bpjs_jkk_employer'])),
            'bpjs_jkm_employer':  Decimal(str(bpjs['bpjs_jkm_employer'])),
            'bpjs_jht_employee':  Decimal(str(bpjs['bpjs_jht_employee'])),
            'bpjs_jht_employer':  Decimal(str(bpjs['bpjs_jht_employer'])),
            'bpjs_jp_employee':   Decimal(str(bpjs['bpjs_jp_employee'])),
            'bpjs_jp_employer':   Decimal(str(bpjs['bpjs_jp_employer'])),
            'pph21_amount':       pph21_amount,
            'total_deductions':   total_deductions,
            'net_salary':         net_salary,
            'breakdown':          breakdown,
        }
    )

    # 10. Save tax calculation log (audit trail)
    TaxCalculationLog.objects.update_or_create(
        payroll_item=item,
        defaults={
            'scheme':       pph21_scheme,
            'ptkp_status':  employee.ptkp_status,
            'ptkp_amount':  pph21_result['ptkp_amount'],
            'gross_annual': gross_salary * 12,
            'biaya_jabatan': pph21_result['biaya_jabatan'],
            'pkp_annual':   pph21_result['pkp_annual'],
            'tax_annual':   pph21_result['tax_annual'],
            'tax_monthly':  pph21_amount,
            'detail':       pph21_result['detail'],
        }
    )

    return item
