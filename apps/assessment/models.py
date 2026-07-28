from django.db import models


class Assessment(models.Model):
    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='assessments', verbose_name='Entitas'
    )
    training = models.ForeignKey(
        'training.TrainingProgram', on_delete=models.CASCADE,
        null=True, blank=True, related_name='assessments',
        verbose_name='Program Pelatihan'
    )
    title = models.CharField(max_length=255, verbose_name='Judul Asesmen / Kuis')
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    passing_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=70.0,
        verbose_name='Nilai Kelulusan (%)'
    )
    time_limit = models.PositiveIntegerField(
        default=30, verbose_name='Batas Waktu (Menit)',
        help_text='0 = Tanpa batas waktu'
    )
    is_mandatory = models.BooleanField(default=True, verbose_name='Wajib')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.entity.code})'


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'MCQ', 'Pilihan Ganda'
        TRUE_FALSE = 'TRUE_FALSE', 'Benar / Salah'
        ESSAY = 'ESSAY', 'Essay'

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE,
        related_name='questions', verbose_name='Asesmen'
    )
    text = models.TextField(verbose_name='Teks Pertanyaan')
    question_type = models.CharField(
        max_length=15, choices=QuestionType.choices,
        default=QuestionType.MCQ, verbose_name='Tipe Soal'
    )
    points = models.PositiveSmallIntegerField(default=10, verbose_name='Bobot / Poin')
    order = models.PositiveSmallIntegerField(default=1, verbose_name='Urutan Soal')

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order', 'id']

    def __str__(self):
        return f'Soal: {self.text[:50]}'


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE,
        related_name='choices', verbose_name='Pertanyaan'
    )
    text = models.CharField(max_length=255, verbose_name='Teks Opsi Jawaban')
    is_correct = models.BooleanField(default=False, verbose_name='Kunci Jawaban')

    class Meta:
        verbose_name = 'Choice'
        verbose_name_plural = 'Choices'

    def __str__(self):
        return f'{self.text} ({"Kunci" if self.is_correct else "Salah"})'


class AssessmentAttempt(models.Model):
    participant = models.ForeignKey(
        'training.TrainingParticipant', on_delete=models.CASCADE,
        null=True, blank=True, related_name='assessment_attempts',
        verbose_name='Peserta Pelatihan'
    )
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE,
        related_name='attempts', verbose_name='Asesmen'
    )
    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='assessment_attempts', verbose_name='Karyawan'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Waktu Mulai')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Waktu Selesai')
    score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Total Skor (%)'
    )
    is_passed = models.BooleanField(default=False, verbose_name='Lulus')
    answers = models.JSONField(default=dict, verbose_name='Detail Jawaban Karyawan')

    class Meta:
        verbose_name = 'Assessment Attempt'
        verbose_name_plural = 'Assessment Attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.employee.full_name} — {self.assessment.title} ({self.score or "Pending"}%)'

