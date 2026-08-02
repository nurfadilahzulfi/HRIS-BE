from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Max
from django.utils import timezone
from django.db import transaction


class Department(models.Model):
    entity = models.ForeignKey(
        'company.Entity',
        on_delete=models.PROTECT,
        related_name='departments',
        verbose_name='Entitas',
    )
    name        = models.CharField(max_length=100, verbose_name='Nama Departemen')
    code        = models.CharField(max_length=20, blank=True, verbose_name='Kode Departemen')
    head        = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='headed_departments',
        verbose_name='Kepala Departemen',
    )
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    is_active   = models.BooleanField(default=True, verbose_name='Aktif')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Department'
        verbose_name_plural = 'Departments'
        unique_together     = [('entity', 'name')]
        ordering            = ['name']

    def __str__(self):
        return f'{self.name} ({self.entity.code})'


class Position(models.Model):
    department  = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='positions',
        verbose_name='Departemen',
    )
    name        = models.CharField(max_length=100, verbose_name='Nama Jabatan')
    grade_level = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Level Grade',
        help_text='Semakin tinggi angka, semakin tinggi jabatan',
    )
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    is_active   = models.BooleanField(default=True, verbose_name='Aktif')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Position'
        verbose_name_plural = 'Positions'
        ordering            = ['-grade_level', 'name']

    def __str__(self):
        return f'{self.name} — {self.department.name}'


class Employee(models.Model):
    class Gender(models.TextChoices):
        MALE   = 'M', 'Laki-laki'
        FEMALE = 'F', 'Perempuan'

    class MaritalStatus(models.TextChoices):
        SINGLE   = 'TK', 'Tidak Kawin'
        MARRIED  = 'K',  'Kawin'
        DIVORCED = 'D',  'Cerai'

    class Status(models.TextChoices):
        ACTIVE     = 'ACTIVE',     'Aktif'
        INACTIVE   = 'INACTIVE',   'Tidak Aktif'
        TERMINATED = 'TERMINATED', 'PHK / Keluar'

    class PTKPStatus(models.TextChoices):
        TK0 = 'TK/0', 'TK/0 - Tidak Kawin, 0 Tanggungan'
        TK1 = 'TK/1', 'TK/1 - Tidak Kawin, 1 Tanggungan'
        TK2 = 'TK/2', 'TK/2 - Tidak Kawin, 2 Tanggungan'
        TK3 = 'TK/3', 'TK/3 - Tidak Kawin, 3 Tanggungan'
        K0  = 'K/0',  'K/0  - Kawin, 0 Tanggungan'
        K1  = 'K/1',  'K/1  - Kawin, 1 Tanggungan'
        K2  = 'K/2',  'K/2  - Kawin, 2 Tanggungan'
        K3  = 'K/3',  'K/3  - Kawin, 3 Tanggungan'

    # ── Identitas & Entitas ────────────────────────────────────────
    entity      = models.ForeignKey(
        'company.Entity',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Entitas',
    )
    user        = models.OneToOneField(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employee_profile',
        verbose_name='Akun Login (User)',
        help_text='Hubungkan ke akun login karyawan ini.',
    )
    employee_id = models.CharField(
        max_length=30, unique=True, blank=True,
        verbose_name='ID Karyawan',
        help_text='Auto-generated: HO-2024-0001',
    )

    # ── Data Pribadi ───────────────────────────────────────────────
    full_name      = models.CharField(max_length=255, verbose_name='Nama Lengkap')
    nik            = models.CharField(
        max_length=16, unique=True,
        validators=[RegexValidator(r'^\d{16}$', 'NIK harus 16 digit angka')],
        verbose_name='NIK KTP'
    )
    gender         = models.CharField(max_length=1, choices=Gender.choices, verbose_name='Jenis Kelamin')
    date_of_birth  = models.DateField(verbose_name='Tanggal Lahir')
    place_of_birth = models.CharField(max_length=100, blank=True, verbose_name='Tempat Lahir')
    religion       = models.CharField(max_length=50, blank=True, verbose_name='Agama')
    blood_type     = models.CharField(max_length=3, blank=True, verbose_name='Golongan Darah')
    marital_status = models.CharField(
        max_length=2, choices=MaritalStatus.choices,
        default=MaritalStatus.SINGLE, verbose_name='Status Pernikahan',
    )
    dependants     = models.PositiveSmallIntegerField(default=0, verbose_name='Jumlah Tanggungan')

    # ── Kontak ─────────────────────────────────────────────────────
    address           = models.TextField(blank=True, verbose_name='Alamat')
    phone             = models.CharField(max_length=20, blank=True, verbose_name='No. Telepon')
    emergency_contact = models.CharField(max_length=100, blank=True, verbose_name='Kontak Darurat')
    photo             = models.ImageField(
        upload_to='employees/photos/',
        null=True, blank=True, verbose_name='Foto',
    )

    # ── Posisi & Struktur Org ──────────────────────────────────────
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees', verbose_name='Departemen',
    )
    position   = models.ForeignKey(
        Position, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='employees', verbose_name='Jabatan',
    )
    manager    = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subordinates', verbose_name='Manager / Atasan',
    )

    # ── Kepegawaian ────────────────────────────────────────────────
    join_date   = models.DateField(verbose_name='Tanggal Bergabung')
    resign_date = models.DateField(null=True, blank=True, verbose_name='Tanggal Keluar')
    status      = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.ACTIVE, verbose_name='Status Karyawan',
    )

    class PPh21Scheme(models.TextChoices):
        GROSS    = 'GROSS',    'Gross (dipotong dari gaji)'
        GROSS_UP = 'GROSS_UP', 'Gross Up (ditanggung perusahaan)'
        NET      = 'NET',      'Net (tidak direfleksikan)'

    # ── Pajak & PTKP ───────────────────────────────────────────────
    npwp         = models.CharField(max_length=25, blank=True, verbose_name='NPWP')
    ptkp_status  = models.CharField(
        max_length=5, choices=PTKPStatus.choices,
        default=PTKPStatus.TK0, verbose_name='Status PTKP',
    )
    pph21_scheme = models.CharField(
        max_length=8,
        choices=PPh21Scheme.choices,
        default=PPh21Scheme.GROSS,
        verbose_name='Skema PPh21',
        help_text='Skema pemotongan PPh21 yang ditanggung karyawan ini',
    )

    # ── BPJS ───────────────────────────────────────────────────────
    bpjs_kes_no = models.CharField(max_length=30, blank=True, verbose_name='No. BPJS Kesehatan')
    bpjs_tk_no  = models.CharField(max_length=30, blank=True, verbose_name='No. BPJS Ketenagakerjaan')

    # ── Bank ───────────────────────────────────────────────────────
    bank_name         = models.CharField(max_length=50, blank=True, verbose_name='Nama Bank')
    bank_account_no   = models.CharField(max_length=30, blank=True, verbose_name='No. Rekening')
    bank_account_name = models.CharField(max_length=100, blank=True, verbose_name='Nama Pemilik Rekening')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Employee'
        verbose_name_plural = 'Employees'
        ordering            = ['full_name']
        indexes             = [
            models.Index(fields=['status', 'department', 'entity']),
            models.Index(fields=['status']),
            models.Index(fields=['entity']),
        ]

    def __str__(self):
        return f'{self.employee_id} — {self.full_name}'

    def save(self, *args, **kwargs):
        if not self.employee_id and self.entity:
            with transaction.atomic():
                # select_for_update mengunci baris Entity ini sampai transaksi selesai,
                # jadi request lain yang mau generate ID untuk entity yang sama
                # akan antre, bukan balapan.
                entity = type(self.entity).objects.select_for_update().get(pk=self.entity.pk)
                sequence = entity.next_employee_sequence()
                self.employee_id = entity.generate_employee_id(timezone.now().year, sequence)
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = timezone.now().date()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def get_manager_chain(self):
        """Return list of managers up the hierarchy (loop-safe)."""
        chain, visited, current = [], set(), self.manager
        while current and current.pk not in visited:
            visited.add(current.pk)
            chain.append(current)
            current = current.manager
        return chain
