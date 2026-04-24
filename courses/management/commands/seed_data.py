from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from courses.models import Category, Course, Enrollment, Lesson, Progress
import random
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed database dengan sample data untuk testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Hapus semua data sebelum seed'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing data...")
            Category.objects.all().delete()
            Course.objects.all().delete()
            Enrollment.objects.all().delete()
            Lesson.objects.all().delete()
            Progress.objects.all().delete()

        self.stdout.write("Seeding data...")
        
        # 1. Create test users
        admin_user = User.objects.filter(username='admin').first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
        
        # Create instructors
        instructors = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                username=f'instructor{i}',
                defaults={
                    'email': f'instructor{i}@example.com',
                    'first_name': f'Instructor {i}',
                    'last_name': 'Test',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            instructors.append(user)
        
        # Create students
        students = []
        for i in range(20):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@example.com',
                    'first_name': f'Student {i}',
                    'last_name': 'Test',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            students.append(user)
        
        # 2. Create categories
        categories_data = [
            ('Programming', None),
            ('Web Development', None),
            ('Data Science', None),
            ('Mobile Development', None),
            ('DevOps', None),
            ('Django Courses', 1),  # Parent is Programming
            ('Python Basics', 1),   # Parent is Programming
        ]
        
        categories = {}
        for name, parent_id in categories_data:
            parent = categories.get(parent_id) if parent_id else None
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'parent': parent,
                    'description': f'Category for {name}'
                }
            )
            categories[name] = cat
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(categories)} categories"))
        
        # 3. Create courses
        course_data = [
            ('Django Fundamentals', 'Learn Django basics', 50000, categories['Django Courses'], instructors[0]),
            ('Advanced Django', 'Master Django advanced topics', 75000, categories['Django Courses'], instructors[0]),
            ('Python for Beginners', 'Start your coding journey', 40000, categories['Python Basics'], instructors[1]),
            ('Python Advanced', 'Become a Python expert', 60000, categories['Python Basics'], instructors[1]),
            ('React.js Mastery', 'Learn modern React', 55000, categories.get('Web Development', categories['Programming']), instructors[2]),
            ('Data Analysis with Python', 'Learn pandas and numpy', 65000, categories['Data Science'], instructors[3]),
            ('Machine Learning 101', 'Introduction to ML', 80000, categories['Data Science'], instructors[3]),
            ('Mobile App Development', 'Build iOS and Android apps', 70000, categories['Mobile Development'], instructors[4]),
        ]
        
        courses = []
        for name, desc, price, category, instructor in course_data:
            course, created = Course.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'price': price,
                    'category': category,
                    'instructor': instructor,
                    'is_published': True,
                    'max_students': random.randint(50, 150)
                }
            )
            courses.append(course)
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(courses)} courses"))
        
        # 4. Create enrollments
        enrollment_count = 0
        for course in courses:
            # Enroll 5-15 students per course
            num_students = random.randint(5, 15)
            enrolled_students = random.sample(students, min(num_students, len(students)))
            
            for student in enrolled_students:
                # Check if already enrolled
                if Enrollment.objects.filter(course=course, student=student).exists():
                    continue
                
                role = random.choice(['student', 'student', 'assistant'])  # 66% student, 33% assistant
                try:
                    enrollment, created = Enrollment.objects.get_or_create(
                        course=course,
                        student=student,
                        defaults={
                            'role': role,
                            'is_active': True,
                            'progress_percentage': random.randint(0, 100)
                        }
                    )
                    if created:
                        enrollment_count += 1
                except:
                    pass
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {enrollment_count} enrollments"))
        
        # 5. Create lessons
        lesson_count = 0
        for course in courses:
            # Create 3-5 chapter per course
            num_chapters = random.randint(3, 5)
            
            for chapter_idx in range(num_chapters):
                chapter = Lesson.objects.create(
                    course=course,
                    title=f"Chapter {chapter_idx + 1}: Introduction to Module",
                    order=chapter_idx,
                    description=f"Learn the fundamentals of chapter {chapter_idx + 1}",
                    duration_minutes=random.randint(30, 120),
                    video_url=f"https://youtube.com/watch?v={random.randint(1000000, 9999999)}"
                )
                lesson_count += 1
                
                # Add 2-4 sub-lessons per chapter
                num_lessons = random.randint(2, 4)
                for lesson_idx in range(num_lessons):
                    Lesson.objects.create(
                        course=course,
                        title=f"Lesson {lesson_idx + 1}: {course.name} Topic",
                        order=lesson_idx,
                        parent_lesson=chapter,
                        description="Learn more about this topic",
                        duration_minutes=random.randint(15, 60),
                        video_url=f"https://youtube.com/watch?v={random.randint(1000000, 9999999)}"
                    )
                    lesson_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {lesson_count} lessons"))
        
        # 6. Create progress records
        progress_count = 0
        for enrollment in Enrollment.objects.all()[:50]:  # Limit to first 50 enrollments
            lessons = enrollment.course.lessons.filter(parent_lesson__isnull=False)[:10]
            
            for lesson in lessons:
                is_completed = random.choice([True, False, False])  # 33% completed
                
                progress, created = Progress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={
                        'is_completed': is_completed,
                        'completion_percentage': 100 if is_completed else random.randint(0, 99),
                        'started_at': timezone.now(),
                        'completed_at': timezone.now() if is_completed else None
                    }
                )
                if created:
                    progress_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"✓ Created {progress_count} progress records"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Database seeding completed successfully!"))
        self.stdout.write("\n📊 Summary:")
        self.stdout.write(f"  • Users: {User.objects.count()}")
        self.stdout.write(f"  • Categories: {Category.objects.count()}")
        self.stdout.write(f"  • Courses: {Course.objects.count()}")
        self.stdout.write(f"  • Enrollments: {Enrollment.objects.count()}")
        self.stdout.write(f"  • Lessons: {Lesson.objects.count()}")
        self.stdout.write(f"  • Progress: {Progress.objects.count()}")
