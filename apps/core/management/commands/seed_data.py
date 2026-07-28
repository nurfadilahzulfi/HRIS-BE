from decimal import Decimal
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.company.models import Company, Entity
from apps.employees.models import Department, Position, Employee
from apps.contracts.models import Contract
from apps.attendance.models import WorkSchedule, EmployeeSchedule, AttendanceLog
from apps.leave.models import LeaveType, LeaveBalance, LeaveRequest, LeaveApproval
from apps.payroll.models import PayrollPeriod, PayrollItem, OvertimeRecord
from apps.salary_slip.models import SalarySlip, SignatureConfig
from apps.training.models import TrainingCategory, TrainingProgram, TrainingParticipant
from apps.assessment.models import Assessment, Question, Choice, AssessmentAttempt
from apps.kpi.models import KPITemplate, KPIItem, EmployeeKPIAssignment, EmployeeKPIResultItem
from apps.notifications.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate initial complete test data for PT. Tanimas Resources International HRIS'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Data Seeding for PT. Tanimas Resources International...'))

        # ── 1. Company & Entity ────────────────────────────────────────────────
        company, _ = Company.objects.get_or_create(
            name='Tanimas Resources Group',
            defaults={
                'description': 'Holding Group Enterprise Ketenagakerjaan',
            }
        )

        entity, _ = Entity.objects.get_or_create(
            code='PT-TRI',
            defaults={
                'company': company,
                'name': 'PT. Tanimas Resources International',
                'npwp': '01.234.567.8-012.000',
                'address': 'Gedung Tanimas Tower Lt. 12, Jl. Jend. Sudirman No. 88, Jakarta Selatan',
                'phone': '021-5551234',
                'email': 'info@tanimas.co.id',
                'employee_id_format': '{ENTITY_CODE}-{YEAR}-{SEQ}',
                'leave_approval_levels': 2,
            }
        )

        # Signature Config
        SignatureConfig.objects.get_or_create(
            entity=entity,
            defaults={
                'signer_name': 'Budi Santoso, S.E., M.M.',
                'signer_position': 'Head of Human Capital',
            }
        )

        # ── 2. Departments & Positions ──────────────────────────────────────────
        dept_hr, _ = Department.objects.get_or_create(entity=entity, name='Human Resources', defaults={'code': 'HRD'})
        dept_it, _ = Department.objects.get_or_create(entity=entity, name='Information Technology', defaults={'code': 'ITD'})
        dept_fin, _ = Department.objects.get_or_create(entity=entity, name='Finance & Accounting', defaults={'code': 'FIN'})
        dept_ops, _ = Department.objects.get_or_create(entity=entity, name='Operations & Supply Chain', defaults={'code': 'OPS'})

        pos_hr_mgr, _ = Position.objects.get_or_create(department=dept_hr, name='HR Manager', defaults={'grade_level': 5})
        pos_hr_spv, _ = Position.objects.get_or_create(department=dept_hr, name='HR Supervisor', defaults={'grade_level': 4})
        pos_it_lead, _ = Position.objects.get_or_create(department=dept_it, name='IT Team Lead', defaults={'grade_level': 4})
        pos_dev, _ = Position.objects.get_or_create(department=dept_it, name='Senior Software Engineer', defaults={'grade_level': 3})
        pos_fin_acc, _ = Position.objects.get_or_create(department=dept_fin, name='Senior Accountant', defaults={'grade_level': 3})
        pos_ops_staff, _ = Position.objects.get_or_create(department=dept_ops, name='Operations Staff', defaults={'grade_level': 2})

        # ── 3. Users & Employees ────────────────────────────────────────────────
        # Superadmin User
        admin_user, _ = User.objects.get_or_create(
            username='admin@tanimas.co.id',
            defaults={
                'email': 'admin@tanimas.co.id',
                'full_name': 'Super Administrator',
                'role': User.Role.SUPER_ADMIN,
                'entity': entity,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('Admin123!')
        admin_user.save()

        # Manager Employee
        mgr_user, _ = User.objects.get_or_create(
            username='budi.santoso@tanimas.co.id',
            defaults={
                'email': 'budi.santoso@tanimas.co.id',
                'full_name': 'Budi Santoso',
                'role': User.Role.MANAGER,
                'entity': entity,
            }
        )
        mgr_user.set_password('Password123!')
        mgr_user.save()

        mgr_emp, _ = Employee.objects.get_or_create(
            user=mgr_user,
            defaults={
                'entity': entity,
                'employee_id': 'TRI-2024-0001',
                'nik': '3171011508850001',
                'full_name': 'Budi Santoso',
                'email': 'budi.santoso@tanimas.co.id',
                'phone': '081234567890',
                'department': dept_hr,
                'position': pos_hr_mgr,
                'employment_type': Employee.EmploymentType.PERMANENT,
                'gender': Employee.Gender.MALE,
                'join_date': date(2020, 1, 15),
                'status': Employee.Status.ACTIVE,
                'npwp': '12.345.678.9-012.000',
                'ptkp_status': 'K1',
                'pph21_scheme': 'GROSS_UP',
                'bpjs_kes_no': '0001234567891',
                'bpjs_tk_no': '12345678901',
                'bank_name': 'Bank Mandiri',
                'bank_account_no': '1230009876543',
                'bank_account_name': 'Budi Santoso',
            }
        )

        # Staff 1 (IT Developer)
        emp1_user, _ = User.objects.get_or_create(
            username='andi.wijaya@tanimas.co.id',
            defaults={
                'email': 'andi.wijaya@tanimas.co.id',
                'full_name': 'Andi Wijaya',
                'role': User.Role.EMPLOYEE,
                'entity': entity,
            }
        )
        emp1_user.set_password('Password123!')
        emp1_user.save()

        emp1, _ = Employee.objects.get_or_create(
            user=emp1_user,
            defaults={
                'entity': entity,
                'employee_id': 'TRI-2024-0002',
                'nik': '3171022005920002',
                'full_name': 'Andi Wijaya',
                'email': 'andi.wijaya@tanimas.co.id',
                'phone': '081298765432',
                'department': dept_it,
                'position': pos_dev,
                'manager': mgr_emp,
                'employment_type': Employee.EmploymentType.CONTRACT,
                'gender': Employee.Gender.MALE,
                'join_date': date(2023, 3, 1),
                'status': Employee.Status.ACTIVE,
                'npwp': '98.765.432.1-012.000',
                'ptkp_status': 'TK0',
                'pph21_scheme': 'GROSS',
                'bpjs_kes_no': '0009876543210',
                'bpjs_tk_no': '98765432109',
                'bank_name': 'BCA',
                'bank_account_no': '8830123456',
                'bank_account_name': 'Andi Wijaya',
            }
        )

        # Staff 2 (Accountant)
        emp2_user, _ = User.objects.get_or_create(
            username='siti.rahma@tanimas.co.id',
            defaults={
                'email': 'siti.rahma@tanimas.co.id',
                'full_name': 'Siti Rahmawati',
                'role': User.Role.EMPLOYEE,
                'entity': entity,
            }
        )
        emp2_user.set_password('Password123!')
        emp2_user.save()

        emp2, _ = Employee.objects.get_or_create(
            user=emp2_user,
            defaults={
                'entity': entity,
                'employee_id': 'TRI-2024-0003',
                'nik': '3171031211940003',
                'full_name': 'Siti Rahmawati',
                'email': 'siti.rahma@tanimas.co.id',
                'phone': '081311223344',
                'department': dept_fin,
                'position': pos_fin_acc,
                'manager': mgr_emp,
                'employment_type': Employee.EmploymentType.PERMANENT,
                'gender': Employee.Gender.FEMALE,
                'join_date': date(2022, 6, 15),
                'status': Employee.Status.ACTIVE,
                'npwp': '45.678.912.3-012.000',
                'ptkp_status': 'K0',
                'pph21_scheme': 'NET',
                'bpjs_kes_no': '0005556667778',
                'bpjs_tk_no': '55566677789',
                'bank_name': 'BNI',
                'bank_account_no': '0112233445',
                'bank_account_name': 'Siti Rahmawati',
            }
        )

        # ── 4. Employment Contracts ─────────────────────────────────────────────
        Contract.objects.get_or_create(
            employee=emp1,
            contract_number='PKWT/TRI/2024/002',
            defaults={
                'contract_type': Contract.ContractType.PKWT,
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 12, 31),
                'basic_salary': Decimal('12500000.00'),
                'status': Contract.Status.ACTIVE,
            }
        )

        Contract.objects.get_or_create(
            employee=emp2,
            contract_number='PKWTT/TRI/2022/003',
            defaults={
                'contract_type': Contract.ContractType.PKWTT,
                'start_date': date(2022, 6, 15),
                'basic_salary': Decimal('11000000.00'),
                'status': Contract.Status.ACTIVE,
            }
        )

        # ── 5. Attendance & Work Schedule ───────────────────────────────────────
        sched, _ = WorkSchedule.objects.get_or_create(
            entity=entity,
            name='Jam Kerja Reguler HO',
            defaults={
                'work_start': time(8, 0),
                'work_end': time(17, 0),
                'break_duration': 60,
            }
        )

        for emp in [mgr_emp, emp1, emp2]:
            EmployeeSchedule.objects.get_or_create(
                employee=emp,
                schedule=sched,
                defaults={'effective_from': date(2024, 1, 1)}
            )

        # Sample Attendance Logs for 5 days
        today = date.today()
        for i in range(1, 6):
            log_date = today - timedelta(days=i)
            if log_date.weekday() < 5:  # Monday to Friday
                AttendanceLog.objects.get_or_create(
                    employee=emp1,
                    date=log_date,
                    defaults={
                        'check_in': time(7, 55),
                        'check_out': time(17, 10),
                        'source': 'FINGER',
                        'late_minutes': 0,
                        'early_minutes': 0,
                        'work_minutes': 495,
                    }
                )
                AttendanceLog.objects.get_or_create(
                    employee=emp2,
                    date=log_date,
                    defaults={
                        'check_in': time(8, 15),
                        'check_out': time(17, 0),
                        'source': 'FINGER',
                        'late_minutes': 15,
                        'early_minutes': 0,
                        'work_minutes': 465,
                    }
                )

        # ── 6. Leave Types, Balances & Requests ─────────────────────────────────
        lt_annual, _ = LeaveType.objects.get_or_create(
            entity=entity,
            name='Cuti Tahunan',
            defaults={'max_days_per_year': 12, 'is_paid': True}
        )

        lt_sick, _ = LeaveType.objects.get_or_create(
            entity=entity,
            name='Cuti Sakit (Surat Dokter)',
            defaults={'max_days_per_year': 14, 'is_paid': True, 'requires_attachment': True}
        )

        for emp in [mgr_emp, emp1, emp2]:
            LeaveBalance.objects.get_or_create(
                employee=emp,
                leave_type=lt_annual,
                year=2026,
                defaults={'allocated': 12, 'used': 2}
            )

        leave_req, _ = LeaveRequest.objects.get_or_create(
            employee=emp1,
            start_date=today + timedelta(days=5),
            defaults={
                'leave_type': lt_annual,
                'end_date': today + timedelta(days=6),
                'total_days': Decimal('2.0'),
                'reason': 'Keperluan keluarga di luar kota',
                'status': LeaveRequest.Status.APPROVED,
                'submitted_at': timezone.now(),
            }
        )

        # ── 7. Overtime Records ────────────────────────────────────────────────
        OvertimeRecord.objects.get_or_create(
            employee=emp1,
            date=today - timedelta(days=2),
            defaults={
                'hours': Decimal('3.0'),
                'hourly_rate': Decimal('72254.33'),
                'calculated_amount': Decimal('325144.50'),
                'reason': 'Deploy rilis backend HRIS ke server staging',
                'status': OvertimeRecord.Status.APPROVED,
            }
        )

        # ── 8. Payroll Period & Calculation ─────────────────────────────────────
        period, _ = PayrollPeriod.objects.get_or_create(
            entity=entity,
            year=2026,
            month=7,
            defaults={
                'name': 'Payroll Juli 2026',
                'start_date': date(2026, 7, 1),
                'end_date': date(2026, 7, 31),
                'status': PayrollPeriod.Status.COMPLETED,
            }
        )

        p_item1, _ = PayrollItem.objects.get_or_create(
            period=period,
            employee=emp1,
            defaults={
                'basic_salary': Decimal('12500000.00'),
                'total_fixed_allowances': Decimal('1500000.00'),
                'total_overtime': Decimal('325144.50'),
                'gross_salary': Decimal('14325144.50'),
                'bpjs_kes_employee': Decimal('125000.00'),
                'bpjs_jht_employee': Decimal('250000.00'),
                'bpjs_jp_employee': Decimal('125000.00'),
                'pph21_amount': Decimal('645000.00'),
                'total_deductions': Decimal('1145000.00'),
                'net_salary': Decimal('13180144.50'),
                'is_finalized': True,
                'breakdown': {
                    'components': [
                        {'name': 'Tunjangan Transport & Makan', 'type': 'EARNING', 'amount': 1500000.00}
                    ]
                }
            }
        )

        # ── 9. Salary Slip ──────────────────────────────────────────────────────
        SalarySlip.objects.get_or_create(
            payroll_item=p_item1,
            defaults={
                'slip_number': 'SLIP/PT-TRI/202607/0001',
                'is_signed': True,
                'generated_at': timezone.now(),
            }
        )

        # ── 10. Training & Assessment ───────────────────────────────────────────
        t_cat, _ = TrainingCategory.objects.get_or_create(entity=entity, name='Technical & IT', defaults={'description': 'Pelatihan Keterampilan Teknikal'})

        t_prog, _ = TrainingProgram.objects.get_or_create(
            entity=entity,
            title='Enterprise Django Architecture & Security Best Practices',
            defaults={
                'category': t_cat,
                'trainer': 'Dr. Ir. Hendra Wijaya, M.T.',
                'start_date': date(2026, 8, 10),
                'end_date': date(2026, 8, 12),
                'location': 'Training Room A, Tanimas Tower',
                'max_participants': 20,
                'status': TrainingProgram.Status.UPCOMING,
            }
        )

        TrainingParticipant.objects.get_or_create(
            program=t_prog,
            employee=emp1,
            defaults={'status': 'CONFIRMED', 'attendance': 'HADIR'}
        )

        asm, _ = Assessment.objects.get_or_create(
            entity=entity,
            training=t_prog,
            title='Post-Test Sertifikasi Internal Django HRIS',
            defaults={'passing_score': Decimal('75.00'), 'time_limit': 45}
        )

        q1, _ = Question.objects.get_or_create(
            assessment=asm,
            text='Manakah metode skema pemotongan PPh21 di mana pajak ditanggung penuh oleh perusahaan?',
            defaults={'question_type': 'MCQ', 'points': 50, 'order': 1}
        )

        Choice.objects.get_or_create(question=q1, text='Gross', defaults={'is_correct': False})
        Choice.objects.get_or_create(question=q1, text='Gross Up', defaults={'is_correct': True})
        Choice.objects.get_or_create(question=q1, text='Net', defaults={'is_correct': False})

        AssessmentAttempt.objects.get_or_create(
            assessment=asm,
            employee=emp1,
            defaults={
                'started_at': timezone.now() - timedelta(minutes=30),
                'submitted_at': timezone.now(),
                'score': Decimal('100.00'),
                'is_passed': True,
                'answers': {str(q1.id): 'Gross Up'},
            }
        )

        # ── 11. KPI Template, Assignments & Results ─────────────────────────────
        kpi_tpl, _ = KPITemplate.objects.get_or_create(
            entity=entity,
            department=dept_it,
            title='KPI Software Developer Q3 2026',
            defaults={'period_type': 'QUARTERLY'}
        )

        kpi_item1, _ = KPIItem.objects.get_or_create(
            template=kpi_tpl,
            indicator='Ketepatan Waktu Delivery Feature / Sprint Objective',
            defaults={'target': Decimal('100.00'), 'unit': '%', 'weight': Decimal('60.00')}
        )

        kpi_item2, _ = KPIItem.objects.get_or_create(
            template=kpi_tpl,
            indicator='Code Quality & Zero Critical Bug Production',
            defaults={'target': Decimal('100.00'), 'unit': '%', 'weight': Decimal('40.00')}
        )

        kpi_assign, _ = EmployeeKPIAssignment.objects.get_or_create(
            employee=emp1,
            template=kpi_tpl,
            period_year=2026,
            period_index=3,
            defaults={
                'status': EmployeeKPIAssignment.Status.FINAL,
                'final_score': Decimal('95.00'),
                'evaluator_notes': 'Kinerja sangat baik, penyelesaian backend HRIS tepat waktu.',
            }
        )

        EmployeeKPIResultItem.objects.get_or_create(
            assignment=kpi_assign,
            kpi_item=kpi_item1,
            defaults={'actual_achievement': Decimal('95.00'), 'score': Decimal('57.00')}
        )
        EmployeeKPIResultItem.objects.get_or_create(
            assignment=kpi_assign,
            kpi_item=kpi_item2,
            defaults={'actual_achievement': Decimal('95.00'), 'score': Decimal('38.00')}
        )

        # ── 12. Notification ───────────────────────────────────────────────────
        Notification.objects.get_or_create(
            recipient=emp1_user,
            title='Slip Gaji Periode Juli 2026 Siap Diunduh',
            defaults={
                'notification_type': Notification.Type.PAYROLL_READY,
                'message': 'Slip gaji Anda untuk periode Juli 2026 telah digenerate.',
                'is_read': False,
            }
        )

        self.stdout.write(self.style.SUCCESS('🎉 SEED DATA SUCCESSFUL! All modules populated with complete test records.'))
        self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
        self.stdout.write(self.style.SUCCESS('🔑 Test Login Credentials:'))
        self.stdout.write(self.style.SUCCESS('   • Superadmin : admin@tanimas.co.id / Admin123!'))
        self.stdout.write(self.style.SUCCESS('   • Manager    : budi.santoso@tanimas.co.id / Password123!'))
        self.stdout.write(self.style.SUCCESS('   • Staff IT   : andi.wijaya@tanimas.co.id / Password123!'))
        self.stdout.write(self.style.SUCCESS('   • Staff Fin  : siti.rahma@tanimas.co.id / Password123!'))
        self.stdout.write(self.style.SUCCESS('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'))
