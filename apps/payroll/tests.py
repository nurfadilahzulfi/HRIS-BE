from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from apps.company.models import Company, Entity
from apps.employees.models import Employee
from apps.payroll.models import OvertimeRecord


class OvertimeRecordTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company", npwp="12345")
        self.entity = Entity.objects.create(company=self.company, name="Test Entity", code="HO")
        self.employee = Employee.objects.create(
            entity=self.entity,
            full_name="Overtime Test Karyawan",
            nik="9876543210987654",
            gender="M",
            date_of_birth=timezone.now().date(),
            join_date=timezone.now().date(),
            status=Employee.Status.ACTIVE,
        )

    def test_calculate_amount_decimal_precision(self):
        ot = OvertimeRecord(
            employee=self.employee,
            date=timezone.now().date(),
            hours_worked=Decimal("2.0"),
            overtime_type=OvertimeRecord.OvertimeType.WEEKDAY,
        )
        monthly_salary = Decimal("5000000.00")
        amount = ot.calculate_amount(monthly_salary)

        # hourly_rate = 5000000 / 173 = 28901.7341...
        # 1st hour (1.5x) = 43352.6011...
        # 2nd hour (2x) = 57803.4682...
        # Total = 101156.07
        self.assertIsInstance(amount, Decimal)
        self.assertEqual(amount, Decimal("101156.07"))
