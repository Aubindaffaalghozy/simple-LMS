from django.db import models
from django.db.models import Count, Prefetch, Q, F


class CourseQuerySet(models.QuerySet):
    """Custom QuerySet untuk Course model dengan optimized queries"""
    
    def for_listing(self):
        """
        Optimized query untuk list view - menggunakan select_related untuk instructor
        dan prefetch_related untuk enrollments dengan annotation
        """
        return self.select_related(
            'instructor',
            'category'
        ).annotate(
            student_count=Count('enrollments', filter=Q(enrollments__role='student', enrollments__is_active=True))
        ).annotate(
            lesson_count=Count('lessons')
        ).order_by('-created_at')
    
    def for_dashboard(self):
        """Optimized untuk dashboard - menampilkan published courses dengan stats"""
        return self.filter(
            is_published=True
        ).select_related(
            'instructor',
            'category'
        ).annotate(
            student_count=Count('enrollments', filter=Q(enrollments__role='student', enrollments__is_active=True)),
            lesson_count=Count('lessons'),
            avg_price=models.Sum('price')
        ).order_by('-created_at')
    
    def for_instructor(self, instructor):
        """Filter courses untuk specific instructor dengan optimized queries"""
        return self.filter(
            instructor=instructor
        ).select_related(
            'category'
        ).annotate(
            student_count=Count('enrollments', filter=Q(enrollments__role='student'))
        )
    
    def by_category(self, category):
        """Filter courses oleh category dan subcategories"""
        categories = [category]
        # Include subcategories
        subcats = category.subcategories.all()
        for subcat in subcats:
            categories.append(subcat)
        
        return self.filter(
            category__in=categories
        ).select_related('instructor', 'category').annotate(
            student_count=Count('enrollments', filter=Q(enrollments__is_active=True))
        )
    
    def popular(self, limit=5):
        """5 kursus paling populer berdasarkan jumlah siswa"""
        return self.annotate(
            student_count=Count('enrollments', filter=Q(enrollments__is_active=True))
        ).order_by('-student_count')[:limit]


class CourseManager(models.Manager):
    """Custom manager untuk Course model"""
    
    def get_queryset(self):
        return CourseQuerySet(self.model, using=self._db)
    
    def for_listing(self):
        return self.get_queryset().for_listing()
    
    def for_dashboard(self):
        return self.get_queryset().for_dashboard()
    
    def for_instructor(self, instructor):
        return self.get_queryset().for_instructor(instructor)
    
    def by_category(self, category):
        return self.get_queryset().by_category(category)
    
    def popular(self, limit=5):
        return self.get_queryset().popular(limit)


class EnrollmentQuerySet(models.QuerySet):
    """Custom QuerySet untuk Enrollment model"""
    
    def for_student_dashboard(self, student):
        """Optimized query untuk dashboard siswa dengan progress tracking"""
        return self.filter(
            student=student,
            is_active=True
        ).select_related(
            'course__instructor',
            'course__category'
        ).annotate(
            total_lessons=Count('course__lessons'),
            completed_lessons=Count('progress_records', filter=Q(progress_records__is_completed=True))
        ).order_by('-enrolled_at')
    
    def active_students(self):
        """Hanya students yang aktif"""
        return self.filter(
            role='student',
            is_active=True
        )
    
    def by_course(self, course):
        """Enrollments per course dengan optimized queries"""
        return self.filter(
            course=course
        ).select_related(
            'student'
        ).order_by('role', 'enrolled_at')
    
    def with_progress(self):
        """Include progress data untuk setiap enrollment"""
        return self.select_related(
            'course__instructor',
            'student'
        ).prefetch_related(
            'progress_records__lesson'
        )


class EnrollmentManager(models.Manager):
    """Custom manager untuk Enrollment model"""
    
    def get_queryset(self):
        return EnrollmentQuerySet(self.model, using=self._db)
    
    def for_student_dashboard(self, student):
        return self.get_queryset().for_student_dashboard(student)
    
    def active_students(self):
        return self.get_queryset().active_students()
    
    def by_course(self, course):
        return self.get_queryset().by_course(course)
    
    def with_progress(self):
        return self.get_queryset().with_progress()


class LessonQuerySet(models.QuerySet):
    """Custom QuerySet untuk Lesson model"""
    
    def for_course(self, course):
        """Lessons per course dengan optional sub-lessons"""
        return self.filter(
            course=course,
            parent_lesson__isnull=True  # Only parent lessons
        ).order_by('order')
    
    def with_sub_lessons(self, course):
        """Courses dengan sub-lessons menggunakan prefetch"""
        lessons = self.filter(
            course=course,
            parent_lesson__isnull=True
        ).prefetch_related(
            Prefetch('sub_lessons', Lesson.objects.all().order_by('order'))
        ).order_by('order')
        return lessons


class LessonManager(models.Manager):
    """Custom manager untuk Lesson model"""
    
    def get_queryset(self):
        return LessonQuerySet(self.model, using=self._db)
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def with_sub_lessons(self, course):
        return self.get_queryset().with_sub_lessons(course)


class ProgressQuerySet(models.QuerySet):
    """Custom QuerySet untuk Progress model"""
    
    def for_enrollment(self, enrollment):
        """Progress tracking untuk spesific enrollment"""
        return self.filter(
            enrollment=enrollment
        ).select_related(
            'lesson'
        ).order_by('lesson__order')
    
    def completed(self):
        """Hanya progress yang sudah completed"""
        return self.filter(is_completed=True)
    
    def incomplete(self):
        """Hanya progress yang belum completed"""
        return self.filter(is_completed=False)
    
    def by_course(self, course):
        """Progress untuk semua lessons dalam course"""
        return self.filter(
            lesson__course=course
        ).select_related(
            'enrollment__student',
            'lesson'
        )


class ProgressManager(models.Manager):
    """Custom manager untuk Progress model"""
    
    def get_queryset(self):
        return ProgressQuerySet(self.model, using=self._db)
    
    def for_enrollment(self, enrollment):
        return self.get_queryset().for_enrollment(enrollment)
    
    def completed(self):
        return self.get_queryset().completed()
    
    def incomplete(self):
        return self.get_queryset().incomplete()
    
    def by_course(self, course):
        return self.get_queryset().by_course(course)
