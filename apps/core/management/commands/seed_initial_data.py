from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import User
from apps.company.models import Company, Entity
from apps.tax.models import PTKP, PPh21Bracket
from apps.leave.models import LeaveType
from apps.payroll.models import SalaryComponent


class Command(BaseCommand):
    help = 'Seeds initial data for PTKP, PPh21 Brackets, Companies, Entities, and Superadmin'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding initial data...'))

        # 1. PTKP 2024
        ptkp_data = [
            ('TK/0', Decimal('54000000')),
            ('TK/1', Decimal('58500000')),
            ('TK/2', Decimal('63000000')),
            ('TK/3', Decimal('67500000')),
            ('K/0',  Decimal('58500000')),
            ('K/1',  Decimal('63000000')),
            ('K/2',  Decimal('67500000')),
            ('K/3',  Decimal('72000000')),
        ]
        for code, amount in ptkp_data:
            PTKP.objects.get_or_create(year=2024, status_code=code, defaults={'amount': amount})
        self.stdout.write(self.style.SUCCESS('✓ PTKP 2024 seeded.'))

        # 2. PPh21 Brackets UU HPP 2021
        brackets_2024 = [
            (Decimal('0'),          Decimal('60000000'),   Decimal('5.00')),
            (Decimal('60000000'),   Decimal('250000000'),  Decimal('15.00')),
            (Decimal('250000000'),  Decimal('500000000'),  Decimal('25.00')),
            (Decimal('500000000'),  Decimal('5000000000'), Decimal('30.00')),
            (Decimal('5000000000'), None,                  Decimal('35.00')),
        ]
        for f, t, rate in brackets_2024:
            PPh21Bracket.objects.get_or_create(year=2024, income_from=f, defaults={'income_to': t, 'rate': rate})
        self.stdout.write(self.style.SUCCESS('✓ PPh21 Brackets 2024 seeded.'))

        # 3. Default Holding & Entity
        company, _ = Company.objects.get_or_create(
            name='Enterprise Corporate Group',
            defaults={
                'address': 'Jakarta, Indonesia',
                'npwp': '01.234.567.8-012.000',
            }
        )
        entity, _ = Entity.objects.get_or_create(
            code='HO',
            defaults={
                'company': company,
                'name': 'Head Office Jakarta',
                'employee_id_format': '{ENTITY_CODE}-{YEAR}-{SEQ}',
                'leave_approval_levels': 2,
            }
        )
        self.stdout.write(self.style.SUCCESS('✓ Default Company & Entity (HO) seeded.'))

        # 4. Leave Types for Head Office
        leave_types = [
            ('Cuti Tahunan', 12, True, 'ALL', False, False, 6),
            ('Cuti Melahirkan', 90, True, 'ALL', False, True, 0),
            ('Cuti Sakit', 14, True, 'ALL', False, True, 0),
            ('Cuti Alasan Penting', 3, True, 'ALL', False, False, 0),
        ]
        for name, days, paid, app, half, req, carry in leave_types:
            LeaveType.objects.get_or_create(
                entity=entity, name=name,
                defaults={
                    'max_days_per_year': days,
                    'is_paid': paid,
                    'applicable_to': app,
                    'allow_halfday': half,
                    'requires_attachment': req,
                    'carry_forward_days': carry,
                }
            )
        self.stdout.write(self.style.SUCCESS('✓ Leave Types seeded.'))

        # 5. Salary Components
        components = [
            ('Tunjangan Jabatan', 'EARNING', True, True, 'FIXED', Decimal('1500000')),
            ('Tunjangan Makan & Transport', 'EARNING', True, True, 'FIXED', Decimal('1000000')),
            ('Bonus Performa', 'EARNING', True, False, 'FIXED', Decimal('0')),
            ('Potongan Keterlambatan', 'DEDUCTION', False, False, 'FIXED', Decimal('0')),
        ]
        for name, ctype, taxable, fixed, ftype, fval in components:
            SalaryComponent.objects.get_or_create(
                entity=entity, name=name,
                defaults={
                    'component_type': ctype,
                    'is_taxable': taxable,
                    'is_fixed': fixed,
                    'formula_type': ftype,
                    'formula_value': fval,
                }
            )
        self.stdout.write(self.style.SUCCESS('✓ Salary Components seeded.'))

        self.stdout.write(self.style.SUCCESS('🎉 Initial Seeding Complete!'))
