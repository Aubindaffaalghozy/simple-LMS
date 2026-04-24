from django.core.management.base import BaseCommand
from django.db import connection, reset_queries
from django.conf import settings
from courses.models import Course, Enrollment, Lesson, Progress
import time


class Command(BaseCommand):
    help = 'Demo query optimization - menunjukkan N+1 problem dan solusinya'

    def handle(self, *args, **options):
        # Enable query debugging
        settings.DEBUG = True
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("DJANGO QUERY OPTIMIZATION DEMO")
        self.stdout.write("="*70)
        
        # ============================================================
        # DEMO 1: List Courses dengan Instructor - N+1 Problem
        # ============================================================
        self.stdout.write("\n" + "-"*70)
        self.stdout.write("DEMO 1: List Courses dengan Instructor")
        self.stdout.write("-"*70)
        
        # ❌ BAD: N+1 Problem
        self.benchmark(
            "❌ BAD - N+1 Problem (akses instructor di loop)",
            self._bad_course_list
        )
        
        # ✅ GOOD: Menggunakan select_related
        self.benchmark(
            "✅ GOOD - Menggunakan select_related",
            self._good_course_list
        )
        
        # ============================================================
        # DEMO 2: List Enrollments dengan Notification Count
        # ============================================================
        self.stdout.write("\n" + "-"*70)
        self.stdout.write("DEMO 2: Enrollments dengan Student + Course Info")
        self.stdout.write("-"*70)
        
        # ❌ BAD: Query individual untuk setiap enrollment
        self.benchmark(
            "❌ BAD - Separate queries",
            self._bad_enrollment_list
        )
        
        # ✅ GOOD: select_related untuk foreign keys
        self.benchmark(
            "✅ GOOD - select_related",
            self._good_enrollment_list
        )
        
        # ============================================================
        # DEMO 3: Course dengan Student Count
        # ============================================================
        self.stdout.write("\n" + "-"*70)
        self.stdout.write("DEMO 3: Course dengan Student Count")
        self.stdout.write("-"*70)
        
        # ❌ BAD: Query count dalam loop
        self.benchmark(
            "❌ BAD - Count query di loop",
            self._bad_course_with_count
        )
        
        # ✅ GOOD: Menggunakan annotate
        self.benchmark(
            "✅ GOOD - Menggunakan annotate(Count())",
            self._good_course_with_count
        )
        
        # ============================================================
        # DEMO 4: Lessons dengan Progress tracking
        # ============================================================
        self.stdout.write("\n" + "-"*70)
        self.stdout.write("DEMO 4: Enrollments dengan Lesson Progress")
        self.stdout.write("-"*70)
        
        # ❌ BAD: Separate queries untuk progress
        self.benchmark(
            "❌ BAD - N+1 untuk progress",
            self._bad_enrollment_progress
        )
        
        # ✅ GOOD: prefetch_related
        self.benchmark(
            "✅ GOOD - Menggunakan prefetch_related",
            self._good_enrollment_progress
        )
        
        # ============================================================
        # SUMMARY
        # ============================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("SUMMARY & KEY TAKEAWAYS")
        self.stdout.write("="*70)
        self.stdout.write("""
✅ OPTIMIZATION TIPS:
1. Gunakan select_related() untuk ForeignKey dan OneToOne
   - Menggunakan SQL JOIN
   - Menghasilkan 1 query besar
   
2. Gunakan prefetch_related() untuk ManyToMany dan Reverse FK
   - Menggunakan N+1 queries yang dioptimasi
   - Menggabungkan di Python
   
3. Gunakan annotate() dan aggregate() untuk hitungan
   - SELECT COUNT(*) FROM ...
   - Bukan loop dengan .count()
   
4. Gunakan select_related().prefetch_related()
   - Kombinasi keduanya untuk relasi kompleks
   - Menghasilkan query yang sangat efisien
   
5. Profiling dengan Django Silk
   - Lihat actual queries di dashboard
   - Identifikasi bottleneck
        """)

    def benchmark(self, label, func):
        """Utility untuk benchmark query"""
        reset_queries()
        
        start_time = time.time()
        result = func()
        elapsed = (time.time() - start_time) * 1000  # ms
        
        query_count = len(connection.queries)
        
        self.stdout.write(f"\n{label}")
        self.stdout.write(f"  Queries: {query_count}")
        self.stdout.write(f"  Time: {elapsed:.2f}ms")
        
        if query_count > 10:
            self.stdout.write(f"  ⚠ WARNING: Too many queries!")
        
        if result:
            self.stdout.write(f"  Result: {result[:1] if isinstance(result, list) else result}")
    
    # ============================================================
    # BAD IMPLEMENTATIONS (N+1 Problem)
    # ============================================================
    
    def _bad_course_list(self):
        """❌ BAD: Mengakses instructor di loop"""
        courses = Course.objects.all()
        data = []
        for course in courses:
            data.append({
                'name': course.name,
                'instructor': course.instructor.get_full_name(),  # Extra query!
            })
        return data
    
    def _bad_enrollment_list(self):
        """❌ BAD: Query course dan student terpisah"""
        enrollments = Enrollment.objects.all()[:10]
        data = []
        for enrollment in enrollments:
            course = Course.objects.get(pk=enrollment.course_id)  # Extra query
            student = enrollment.student  # Extra query
            data.append({
                'course': course.name,
                'student': student.username,
            })
        return data
    
    def _bad_course_with_count(self):
        """❌ BAD: Count di dalam loop"""
        courses = Course.objects.all()
        data = []
        for course in courses:
            count = Enrollment.objects.filter(course=course).count()  # Extra query per course!
            data.append({
                'name': course.name,
                'students': count,
            })
        return data
    
    def _bad_enrollment_progress(self):
        """❌ BAD: N+1 untuk progress"""
        enrollments = Enrollment.objects.all()[:5]
        data = []
        for enrollment in enrollments:
            lessons = enrollment.course.lessons.all()  # Query per enrollment
            progress_list = []
            for lesson in lessons:
                progress = Progress.objects.filter(
                    enrollment=enrollment,
                    lesson=lesson
                ).first()  # Query per lesson!
                progress_list.append(progress)
            data.append({
                'student': enrollment.student.username,
                'progress': len(progress_list),
            })
        return data
    
    # ============================================================
    # GOOD IMPLEMENTATIONS (Optimized)
    # ============================================================
    
    def _good_course_list(self):
        """✅ GOOD: Menggunakan select_related"""
        courses = Course.objects.select_related('instructor').all()
        data = []
        for course in courses:
            data.append({
                'name': course.name,
                'instructor': course.instructor.get_full_name(),  # No extra query!
            })
        return data
    
    def _good_enrollment_list(self):
        """✅ GOOD: select_related untuk joins"""
        enrollments = Enrollment.objects.select_related(
            'course',
            'student'
        ).all()[:10]
        data = []
        for enrollment in enrollments:
            data.append({
                'course': enrollment.course.name,
                'student': enrollment.student.username,
            })
        return data
    
    def _good_course_with_count(self):
        """✅ GOOD: annotate dengan Count"""
        from django.db.models import Count, Q
        
        courses = Course.objects.annotate(
            student_count=Count('enrollments', filter=Q(enrollments__role='student'))
        ).all()
        data = []
        for course in courses:
            data.append({
                'name': course.name,
                'students': course.student_count,  # Already calculated!
            })
        return data
    
    def _good_enrollment_progress(self):
        """✅ GOOD: select_related + prefetch_related"""
        from django.db.models import Prefetch
        
        enrollments = Enrollment.objects.select_related(
            'course__instructor',
            'student'
        ).prefetch_related(
            Prefetch(
                'progress_records',
                Progress.objects.select_related('lesson')
            )
        ).all()[:5]
        
        data = []
        for enrollment in enrollments:
            data.append({
                'student': enrollment.student.username,
                'progress_count': enrollment.progress_records.count(),
            })
        return data
