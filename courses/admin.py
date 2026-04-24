from django.contrib import admin
from django.db.models import Count, Q
from .models import Category, Course, Enrollment, Lesson, Progress


class CategoryAdmin(admin.ModelAdmin):
    """Admin interface untuk Category model"""
    list_display = ('name', 'parent', 'course_count', 'created_at')
    list_filter = ('created_at', 'parent')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def course_count(self, obj):
        """Display jumlah courses per category"""
        return obj.courses.count()
    course_count.short_description = 'Courses'
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('name', 'description', 'parent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class LessonInline(admin.TabularInline):
    """Inline admin untuk Lesson - bisa langsung edit lessons dari Course"""
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'duration_minutes', 'parent_lesson')
    ordering = ('order',)


class EnrollmentInline(admin.TabularInline):
    """Inline admin untuk Enrollment - lihat students per course"""
    model = Enrollment
    extra = 0
    fields = ('student', 'role', 'is_active', 'progress_percentage', 'enrolled_at')
    readonly_fields = ('enrolled_at',)
    can_delete = True


class CourseAdmin(admin.ModelAdmin):
    """Admin interface untuk Course model"""
    list_display = (
        'name', 
        'instructor', 
        'category', 
        'student_count',
        'lesson_count',
        'price',
        'is_published',
        'created_at'
    )
    list_filter = (
        'is_published',
        'category',
        'instructor',
        'created_at',
        'price'
    )
    search_fields = ('name', 'description', 'instructor__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'course_stats')
    inlines = [LessonInline, EnrollmentInline]
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('name', 'description', 'category', 'instructor')
        }),
        ('Detail Kursus', {
            'fields': ('price', 'max_students', 'is_published', 'image')
        }),
        ('Statistik', {
            'fields': ('course_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_count(self, obj):
        """Display student enrolled count"""
        return obj.enrollments.filter(
            role='student',
            is_active=True
        ).count()
    student_count.short_description = 'Students'
    
    def lesson_count(self, obj):
        """Display total lessons count"""
        return obj.lessons.filter(parent_lesson__isnull=True).count()
    lesson_count.short_description = 'Lessons'
    
    def course_stats(self, obj):
        """Display comprehensive course statistics"""
        students = obj.enrollments.filter(role='student', is_active=True).count()
        assistants = obj.enrollments.filter(role='assistant').count()
        lessons = obj.lessons.filter(parent_lesson__isnull=True).count()
        
        return f"""
        <b>Student Stats:</b><br>
        • Active Students: {students}<br>
        • Assistants: {assistants}<br>
        • Total Lessons: {lessons}<br>
        • Revenue Potential: Rp {students * obj.price:,}
        """
    course_stats.short_description = 'Course Statistics'
    
    def get_queryset(self, request):
        """Optimize queryset dengan select_related dan annotate"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'instructor',
            'category'
        ).annotate(
            _student_count=Count('enrollments', filter=Q(enrollments__role='student'))
        )


class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface untuk Enrollment model"""
    list_display = (
        'student_full_name',
        'course',
        'role',
        'progress_percentage',
        'is_active',
        'enrolled_at'
    )
    list_filter = (
        'role',
        'is_active',
        'course__category',
        'enrolled_at'
    )
    search_fields = ('student__username', 'student__first_name', 'course__name')
    readonly_fields = ('enrolled_at',)
    ordering = ('-enrolled_at',)
    
    fieldsets = (
        ('Enrollment Info', {
            'fields': ('course', 'student', 'role', 'is_active')
        }),
        ('Progress', {
            'fields': ('progress_percentage',)
        }),
        ('Dates', {
            'fields': ('enrolled_at',),
            'classes': ('collapse',)
        }),
    )
    
    def student_full_name(self, obj):
        """Display student full name"""
        return obj.student.get_full_name() or obj.student.username
    student_full_name.short_description = 'Student'
    student_full_name.admin_order_field = 'student__username'
    
    def get_queryset(self, request):
        """Optimize queryset dengan select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('student', 'course').prefetch_related('progress_records')


class ProgressInline(admin.TabularInline):
    """Inline admin untuk Progress"""
    model = Progress
    extra = 0
    fields = ('lesson', 'is_completed', 'completion_percentage', 'started_at', 'completed_at')
    readonly_fields = ('started_at', 'completed_at', 'created_at', 'updated_at')
    can_delete = True


class LessonAdmin(admin.ModelAdmin):
    """Admin interface untuk Lesson model"""
    list_display = (
        'title',
        'course',
        'order',
        'duration_minutes',
        'parent_lesson',
        'has_video',
        'created_at'
    )
    list_filter = (
        'course__category',
        'course',
        'parent_lesson',
        'created_at'
    )
    search_fields = ('title', 'description', 'course__name')
    ordering = ('course', 'order')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProgressInline]
    
    fieldsets = (
        ('Lesson Info', {
            'fields': ('course', 'title', 'order', 'parent_lesson')
        }),
        ('Content', {
            'fields': ('description', 'content', 'video_url', 'attachment')
        }),
        ('Duration', {
            'fields': ('duration_minutes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_video(self, obj):
        """Check apakah lesson memiliki video"""
        return bool(obj.video_url)
    has_video.short_description = 'Has Video'
    has_video.boolean = True
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('course', 'parent_lesson')


class ProgressAdmin(admin.ModelAdmin):
    """Admin interface untuk Progress model"""
    list_display = (
        'student_name',
        'course_name',
        'lesson_title',
        'is_completed',
        'completion_percentage',
        'completed_at'
    )
    list_filter = (
        'is_completed',
        'lesson__course__category',
        'completed_at',
        'created_at'
    )
    search_fields = (
        'enrollment__student__username',
        'lesson__title',
        'lesson__course__name'
    )
    readonly_fields = ('started_at', 'completed_at', 'created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('Progress Info', {
            'fields': ('enrollment', 'lesson', 'is_completed', 'completion_percentage')
        }),
        ('Dates', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )
    
    def student_name(self, obj):
        """Display student name"""
        return obj.enrollment.student.get_full_name() or obj.enrollment.student.username
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'enrollment__student__username'
    
    def course_name(self, obj):
        """Display course name"""
        return obj.lesson.course.name
    course_name.short_description = 'Course'
    course_name.admin_order_field = 'lesson__course__name'
    
    def lesson_title(self, obj):
        """Display lesson title"""
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    lesson_title.admin_order_field = 'lesson__title'
    
    def get_queryset(self, request):
        """Optimize queryset dengan select_related dan prefetch"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'enrollment__student',
            'enrollment__course',
            'lesson'
        )


# Register models di Django Admin
admin.site.register(Category, CategoryAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Progress, ProgressAdmin)

# Customize admin site title dan header
admin.site.site_header = "Simple LMS Administration"
admin.site.site_title = "LMS Admin"
admin.site.index_title = "Welcome to Simple LMS Admin"

