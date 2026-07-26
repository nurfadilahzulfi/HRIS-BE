from django.db import models


class AssessmentTemplate(models.Model):
    entity = models.ForeignKey(
        'company.Entity', on_delete=models.CASCADE,
        related_name='assessment_templates', verbose_name='Entitas'
    )
    title = models.CharField(max_length=255, verbose_name='Judul Asesmen / Kuiz')
    description = models.TextField(blank=True, verbose_name='Deskripsi')
    passing_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=70.0,
        verbose_name='Nilai Kelulusan (Passing Score)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assessment Template'
        verbose_name_plural = 'Assessment Templates'
        ordering = ['title']

    def __str__(self):
        return f'{self.title} ({self.entity.code})'


class Question(models.Model):
    template = models.ForeignKey(
        AssessmentTemplate, on_delete=models.CASCADE,
        related_name='questions', verbose_name='Template Asesmen'
    )
    prompt = models.TextField(verbose_name='Pertanyaan')
    options = models.JSONField(
        default=list, verbose_name='Pilihan Jawaban',
        help_text='JSON List of choices: [{"key": "A", "text": "Opt A"}, ...]'
    )
    correct_answer = models.CharField(
        max_length=50, verbose_name='Kunci Jawaban',
        help_text='Misal: A, B, atau teks jawaban'
    )
    weight = models.PositiveSmallIntegerField(default=1, verbose_name='Bobot Soal')

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f'Soal: {self.prompt[:50]}'


class AssessmentSubmission(models.Model):
    template = models.ForeignKey(
        AssessmentTemplate, on_delete=models.CASCADE,
        related_name='submissions', verbose_name='Template Asesmen'
    )
    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='assessment_submissions', verbose_name='Karyawan'
    )
    answers = models.JSONField(default=dict, verbose_name='Jawaban Karyawan')
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Total Skor'
    )
    is_passed = models.BooleanField(default=False, verbose_name='Lulus')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Assessment Submission'
        verbose_name_plural = 'Assessment Submissions'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.employee.full_name} — {self.template.title} ({self.total_score})'
