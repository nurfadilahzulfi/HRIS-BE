from django.db import models


class TrainingCategory(models.Model):
    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='training_categories', verbose_name='Entitas'
    )
    name = models.CharField(max_length=100, verbose_name='Nama Kategori')
    description = models.TextField(blank=True, verbose_name='Deskripsi')

    class Meta:
        verbose_name = 'Training Category'
        verbose_name_plural = 'Training Categories'
        unique_together = [('entity', 'name')]
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.entity.code})'


class TrainingProgram(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Pendaftaran Dibuka'
        ONGOING = 'ONGOING', 'Berlangsung'
        COMPLETED = 'COMPLETED', 'Selesai'
        CANCELLED = 'CANCELLED', 'Batal'

    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='training_programs', verbose_name='Entitas'
    )
    category = models.ForeignKey(
        TrainingCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='programs',
        verbose_name='Kategori Pelatihan'
    )
    title = models.CharField(max_length=255, verbose_name='Judul Pelatihan')
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    objectives = models.TextField(blank=True, verbose_name='Tujuan Pelatihan')
    trainer = models.CharField(max_length=150, verbose_name='Pelatih / Instruktur')
    location = models.CharField(max_length=255, blank=True, verbose_name='Lokasi')
    start_date = models.DateField(verbose_name='Tanggal Mulai')
    end_date = models.DateField(verbose_name='Tanggal Selesai')
    max_participants = models.PositiveIntegerField(default=0, verbose_name='Maksimal Peserta', help_text='0 = Tidak terbatas')
    material = models.FileField(upload_to='training/materials/', null=True, blank=True, verbose_name='Modul / Materi (PDF)')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT, verbose_name='Status Pelatihan')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Training Program'
        verbose_name_plural = 'Training Programs'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.title} ({self.entity.code})'


class TrainingParticipant(models.Model):
    class Status(models.TextChoices):
        REGISTERED = 'REGISTERED', 'Terdaftar'
        PASSED = 'PASSED', 'Lulus'
        FAILED = 'FAILED', 'Tidak Lulus'
        CANCELLED = 'CANCELLED', 'Batal'

    class Attendance(models.TextChoices):
        REGISTERED = 'REGISTERED', 'Terdaftar'
        ATTENDED = 'ATTENDED', 'Hadir'
        ABSENT = 'ABSENT', 'Tidak Hadir'
        CANCELLED = 'CANCELLED', 'Batal'

    program = models.ForeignKey(
        TrainingProgram, on_delete=models.CASCADE,
        related_name='participants', verbose_name='Program Pelatihan'
    )
    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='training_participations', verbose_name='Karyawan'
    )
    status = models.CharField(
        max_length=15, choices=Status.choices,
        default=Status.REGISTERED, verbose_name='Status Kelulusan'
    )
    attendance = models.CharField(
        max_length=15, choices=Attendance.choices,
        default=Attendance.REGISTERED, verbose_name='Kehadiran'
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Nilai / Skor'
    )
    kpi_snapshot = models.JSONField(
        null=True, blank=True,
        verbose_name='KPI Pre-Training Snapshot',
        help_text='Snapshot KPI aktif karyawan saat didaftarkan ke pelatihan'
    )
    certificate = models.FileField(
        upload_to='training/certificates/', null=True, blank=True,
        verbose_name='Sertifikat'
    )
    notes = models.TextField(blank=True, verbose_name='Catatan Evaluasi')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Waktu Pendaftaran')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Training Participant'
        verbose_name_plural = 'Training Participants'
        unique_together = [('program', 'employee')]

    def __str__(self):
        return f'{self.employee.full_name} — {self.program.title}'

