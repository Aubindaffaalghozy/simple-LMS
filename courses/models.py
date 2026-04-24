from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .managers import CourseManager, EnrollmentManager, LessonManager, ProgressManager


class Category(models.Model):
    """
    Model Category dengan self-referencing untuk membuat hierarchy
    (e.g., Programming > Web Development > Django)
    """
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(default='-')
    parent = models.ForeignKey(
        'self',
        verbose_name='Parent Category',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_category_name'),
            models.Index(fields=['parent'], name='idx_category_parent'),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Course(models.Model):
    """
    Model Course - Mata Kuliah/Kursus
    Dengan relasi ke User (instructor), Category, dan tracking timestamps
    """
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(default='-')
    category = models.ForeignKey(
        Category,
        verbose_name='Category',
        on_delete=models.PROTECT,
        related_name='courses'
    )
    instructor = models.ForeignKey(
        User,
        verbose_name='Instructor',
        on_delete=models.PROTECT,
        related_name='taught_courses'
    )
    price = models.IntegerField(default=0, db_index=True)
    image = models.FileField('Course Image', null=True, blank=True, upload_to='courses/')
    is_published = models.BooleanField(default=False, db_index=True)
    max_students = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CourseManager()

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name'], name='idx_course_name'),
            models.Index(fields=['instructor'], name='idx_course_instructor'),
            models.Index(fields=['category'], name='idx_course_category'),
            models.Index(fields=['price'], name='idx_course_price'),
            models.Index(fields=['is_published', '-created_at'], name='idx_course_published'),
        ]

    def __str__(self):
        return f"{self.name} ({self.instructor.get_full_name()})"

    def get_enrolled_count(self):
        """Get total number of students enrolled"""
        return self.enrollments.filter(role='student').count()


ROLE_CHOICES = (
    ('student', 'Student'),
    ('assistant', 'Assistant'),
    ('instructor', 'Instructor'),
)


class Enrollment(models.Model):
    """
    Model Enrollment - Pendaftaran siswa ke Course
    Dengan unique constraint untuk mencegah duplikasi
    """
    course = models.ForeignKey(
        Course,
        verbose_name='Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    student = models.ForeignKey(
        User,
        verbose_name='Student',
        on_delete=models.CASCADE,
        related_name='course_enrollments'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        db_index=True
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)
    progress_percentage = models.IntegerField(default=0, help_text="Percentage of lessons completed")

    objects = EnrollmentManager()

    class Meta:
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'
        ordering = ['-enrolled_at']
        unique_together = ('course', 'student')
        indexes = [
            models.Index(fields=['course', 'student'], name='idx_enr_course_stud'),
            models.Index(fields=['student', 'is_active'], name='idx_enr_stud_active'),
            models.Index(fields=['course', 'role'], name='idx_enr_course_role'),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.course.name} ({self.role})"

    def clean(self):
        """Validate that course doesn't exceed max_students"""
        if self.student_id and self.course_id:
            active_students = Enrollment.objects.filter(
                course_id=self.course_id,
                role='student',
                is_active=True
            ).exclude(pk=self.pk).count()
            
            if active_students >= self.course.max_students:
                raise ValidationError("Course has reached maximum number of students")


class Lesson(models.Model):
    """
    Model Lesson - Materi pembelajaran per course
    Dengan ordering dan self-referencing untuk hierarchy
    """
    course = models.ForeignKey(
        Course,
        verbose_name='Course',
        on_delete=models.CASCADE,
        related_name='lessons'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(default='-')
    order = models.IntegerField(default=0, db_index=True)
    parent_lesson = models.ForeignKey(
        'self',
        verbose_name='Parent Lesson',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_lessons'
    )
    content = models.TextField(null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    attachment = models.FileField('Attachment', null=True, blank=True, upload_to='lessons/')
    duration_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LessonManager()

    class Meta:
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'
        ordering = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order'], name='idx_lesson_course_ord'),
            models.Index(fields=['parent_lesson'], name='idx_lesson_parent'),
        ]

    def __str__(self):
        if self.parent_lesson:
            return f"{self.course.name} > {self.parent_lesson.title} > {self.title}"
        return f"{self.course.name} > {self.title}"


class Progress(models.Model):
    """
    Model Progress - Tracking penyelesaian lesson oleh student
    """
    enrollment = models.ForeignKey(
        Enrollment,
        verbose_name='Enrollment',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    lesson = models.ForeignKey(
        Lesson,
        verbose_name='Lesson',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProgressManager()

    class Meta:
        verbose_name = 'Progress'
        verbose_name_plural = 'Progresses'
        ordering = ['-updated_at']
        unique_together = ('enrollment', 'lesson')
        indexes = [
            models.Index(fields=['enrollment', 'is_completed'], name='idx_prog_enr_compl'),
            models.Index(fields=['lesson', 'is_completed'], name='idx_prog_les_compl'),
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"[{status}] {self.enrollment.student.username} - {self.lesson.title}"
