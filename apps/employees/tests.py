from django.test import TestCase
from django.utils import timezone
from apps.core.models import User
from apps.company.models import Company, Entity
from apps.employees.models import Employee, Department, Position


class EmployeeSignalTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company", npwp="12345")
        self.entity = Entity.objects.create(company=self.company, name="Test Entity", code="HO")
        self.user = User.objects.create_user(email="testemp@example.com", password="password123")
        self.employee = Employee.objects.create(
            entity=self.entity,
            user=self.user,
            full_name="Test Karyawan",
            nik="1234567890123456",
            gender="M",
            date_of_birth=timezone.now().date(),
            join_date=timezone.now().date(),
            status=Employee.Status.ACTIVE,
        )

    def test_deactivate_user_on_termination(self):
        self.assertTrue(self.user.is_active)
        self.employee.status = Employee.Status.TERMINATED
        self.employee.save()

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
