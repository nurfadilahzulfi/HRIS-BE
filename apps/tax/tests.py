from decimal import Decimal
from django.test import TestCase
from apps.tax.engine import calculate_pph21


class PPh21EngineTestCase(TestCase):
    def test_gross_scheme(self):
        result = calculate_pph21(
            gross_monthly=Decimal('10000000'),
            ptkp_status='TK/0',
            scheme='GROSS',
            year=2024,
            bpjs_employee_monthly=Decimal('300000')
        )
        self.assertIn('tax_monthly', result)
        self.assertGreater(result['tax_monthly'], Decimal('0'))
        self.assertEqual(result['detail']['employee_burden'], float(result['tax_monthly']))
        self.assertEqual(result['detail']['employer_burden'], 0)

    def test_gross_up_scheme(self):
        result = calculate_pph21(
            gross_monthly=Decimal('10000000'),
            ptkp_status='TK/0',
            scheme='GROSS_UP',
            year=2024,
            bpjs_employee_monthly=Decimal('300000')
        )
        self.assertIn('tax_monthly', result)
        self.assertGreater(result['tax_monthly'], Decimal('0'))
        self.assertEqual(result['detail']['employee_burden'], 0)
        self.assertGreater(result['detail']['employer_burden'], 0)

    def test_net_scheme(self):
        result = calculate_pph21(
            gross_monthly=Decimal('10000000'),
            ptkp_status='TK/0',
            scheme='NET',
            year=2024,
            bpjs_employee_monthly=Decimal('300000')
        )
        self.assertEqual(result['tax_monthly'], Decimal('0'))
        self.assertEqual(result['detail']['employee_burden'], 0)
        self.assertGreater(result['detail']['employer_burden'], 0)
