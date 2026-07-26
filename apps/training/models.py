from django.db import models


class TrainingProgram(models.Model):
    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='training_programs', verbose_name='Entitas'
    )
    title = models.CharField(max_length=255, verbose_name='Judul Pelatihan')
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    trainer = models.CharField(max_length=150, verbose_name='Pelatih / Instruktur')
    start_date = models.DateField(verbose_name='Tanggal Mulai')
    end_date = models.DateField(verbose_name='Tanggal Selesai')
    location = models.CharField(max_length=255, blank=True, verbose_name='Lokasi')
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
        default=Status.REGISTERED, verbose_name='Status'
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Nilai / Skor'
    )
    certificate = models.FileField(
        upload_to='training/certificates/', null=True, blank=True,
        verbose_name='Sertifikat'
    )
    notes = models.TextField(blank=True, verbose_name='Catatan Evaluasi')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Training Participant'
        verbose_name_plural = 'Training Participants'
        unique_together = [('program', 'employee')]

    def __str__(self):
        return f'{self.employee.full_name} — {self.program.title}'
