"""
Simple LMS REST API
Django Ninja API with JWT Authentication and RBAC
"""
from typing import List, Optional
from django.contrib.auth.models import User
from django.db.models import Q
from ninja import NinjaAPI, Router, Query, Path
from ninja.errors import HttpError

from courses.models import Course, Category, Enrollment, Lesson, Progress

from .schemas import (
    # Auth
    RegisterIn, LoginIn, TokenOut, TokenRefreshIn, UserOut, UserProfileOut, UserUpdate,
    # Course
    CourseIn, CourseOut, CourseDetailOut, CategoryOut, PaginatedCoursesOut,
    # Enrollment
    EnrollmentIn, EnrollmentOut, EnrollmentListOut, ProgressIn, ProgressOut, PaginatedEnrollmentsOut,
)
from .auth import create_tokens, verify_token, authenticate_user, get_user_from_token
from .rbac import is_instructor, is_admin, is_student, is_enrolled, is_course_owner


# Create API instance
api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="REST API for Simple Learning Management System with JWT Authentication and RBAC"
)

# Create routers
auth_router = Router()
courses_router = Router()
enrollments_router = Router()


# ==================== Helper Functions ====================

def get_pagination_params(page: int = 1, page_size: int = 10):
    """Calculate pagination parameters."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    return page, page_size


def paginate_query(query, page: int, page_size: int):
    """Paginate a queryset."""
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    offset = (page - 1) * page_size
    items = query[offset:offset + page_size]
    return items, total, total_pages


# ==================== Authentication Endpoints ====================

@auth_router.post('/register', response={201: TokenOut}, tags=['Authentication'])
def register(request, data: RegisterIn):
    """Register a new user and return JWT tokens."""
    # Check if username already exists
    if User.objects.filter(username=data.username).exists():
        raise HttpError(400, "Username already exists")
    
    # Check if email already exists
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "Email already exists")
    
    # Create user
    user = User.objects.create_user(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name
    )
    
    # Create tokens
    tokens = create_tokens(user.id)
    return 201, tokens


@auth_router.post('/login', response=TokenOut, tags=['Authentication'])
def login(request, data: LoginIn):
    """Login and return JWT tokens."""
    user = authenticate_user(data.username, data.password)
    
    if user is None:
        raise HttpError(401, "Invalid username or password")
    
    tokens = create_tokens(user.id)
    return tokens


@auth_router.post('/refresh', response=TokenOut, tags=['Authentication'])
def refresh_token(request, data: TokenRefreshIn):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(data.refresh_token, 'refresh')
        user_id = payload.get('user_id')
        
        # Verify user still exists
        user = User.objects.get(pk=user_id)
        tokens = create_tokens(user.id)
        return tokens
    except Exception as e:
        raise HttpError(401, "Invalid refresh token")


@auth_router.get('/me', response=UserProfileOut, tags=['Authentication'])
def get_current_user(request):
    """Get current authenticated user profile."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    return user


@auth_router.put('/me', response=UserProfileOut, tags=['Authentication'])
def update_current_user(request, data: UserUpdate):
    """Update current user profile."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Update fields
    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    if data.email:
        user.email = data.email
    
    user.save()
    return user


# ==================== Course Endpoints (Public) ====================

@courses_router.get('/', response=PaginatedCoursesOut, tags=['Courses'])
def list_courses(
    request,
    search: Optional[str] = Query(None, description="Search by course name"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    min_price: Optional[int] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price"),
    is_published: Optional[bool] = Query(None, description="Filter by published status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """List all courses with pagination and filters."""
    # Start with published courses only for public endpoint
    queryset = Course.objects.select_related('instructor', 'category').filter(is_published=True)
    
    # Apply filters
    if search:
        queryset = queryset.filter(name__icontains=search)
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    if is_published is not None:
        queryset = queryset.filter(is_published=is_published)
    
    # Get pagination
    page, page_size = get_pagination_params(page, page_size)
    items, total, total_pages = paginate_query(queryset, page, page_size)
    
    return {
        'items': list(items),
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@courses_router.get('/{id}', response=CourseDetailOut, tags=['Courses'])
def get_course(request, id: int = Path(..., description="Course ID")):
    """Get course detail by ID."""
    try:
        course = Course.objects.select_related('instructor', 'category').get(pk=id)
        return course
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")


# ==================== Course Endpoints (Protected) ====================

@courses_router.post('/', response={201: CourseOut}, tags=['Courses (Protected)'])
def create_course(request, data: CourseIn):
    """Create a new course (Instructor only)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Check if user is an instructor
    if not is_instructor(user):
        raise HttpError(403, "Instructor role required")
    
    # Verify category exists
    try:
        category = Category.objects.get(pk=data.category_id)
    except Category.DoesNotExist:
        raise HttpError(404, "Category not found")
    
    # Create course
    course = Course.objects.create(
        name=data.name,
        description=data.description,
        category_id=data.category_id,
        price=data.price,
        is_published=data.is_published,
        max_students=data.max_students,
        instructor=user
    )
    
    return 201, course


@courses_router.patch('/{id}', response=CourseOut, tags=['Courses (Protected)'])
def update_course(request, id: int = Path(...), data: CourseIn = None):
    """Update a course (Owner only)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    try:
        course = Course.objects.get(pk=id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    
    # Check ownership or admin
    if not is_course_owner(user, course) and not is_admin(user):
        raise HttpError(403, "Course ownership required")
    
    # Update fields
    if data.name:
        course.name = data.name
    if data.description:
        course.description = data.description
    if data.category_id:
        course.category_id = data.category_id
    if data.price is not None:
        course.price = data.price
    if data.is_published is not None:
        course.is_published = data.is_published
    if data.max_students:
        course.max_students = data.max_students
    
    course.save()
    return course


@courses_router.delete('/{id}', response={204: None}, tags=['Courses (Protected)'])
def delete_course(request, id: int = Path(...)):
    """Delete a course (Admin only)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Only admin can delete
    if not is_admin(user):
        raise HttpError(403, "Admin role required")
    
    try:
        course = Course.objects.get(pk=id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    
    course.delete()
    return 204, None


# ==================== Enrollment Endpoints ====================

@enrollments_router.post('/', response={201: EnrollmentOut}, tags=['Enrollments'])
def enroll_course(request, data: EnrollmentIn):
    """Enroll in a course (Student only)."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Verify course exists
    try:
        course = Course.objects.get(pk=data.course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=user, course=course, is_active=True).exists():
        raise HttpError(400, "Already enrolled in this course")
    
    # Check if course is full
    enrolled_count = course.enrollments.filter(role='student', is_active=True).count()
    if enrolled_count >= course.max_students:
        raise HttpError(400, "Course is full")
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        course=course,
        student=user,
        role='student'
    )
    
    return 201, enrollment


@enrollments_router.get('/my-courses', response=PaginatedEnrollmentsOut, tags=['Enrollments'])
def my_enrolled_courses(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """Get current user's enrolled courses."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Get enrollments
    queryset = Enrollment.objects.filter(
        student=user,
        is_active=True
    ).select_related('course', 'course__instructor', 'course__category')
    
    # Get pagination
    page, page_size = get_pagination_params(page, page_size)
    items, total, total_pages = paginate_query(queryset, page, page_size)
    
    # Transform to simplified format
    enrollment_list = []
    for enrollment in items:
        enrollment_list.append({
            'id': enrollment.id,
            'course_id': enrollment.course.id,
            'course_name': enrollment.course.name,
            'role': enrollment.role,
            'enrolled_at': enrollment.enrolled_at,
            'progress_percentage': enrollment.progress_percentage
        })
    
    return {
        'items': enrollment_list,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@enrollments_router.post('/{id}/progress', response=ProgressOut, tags=['Enrollments'])
def mark_lesson_complete(
    request,
    data: ProgressIn,
    id: int = Path(..., description="Enrollment ID"),
):
    """Mark a lesson as complete."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise HttpError(401, "Authentication required")
    
    token = auth_header.replace('Bearer ', '')
    user = get_user_from_token(token)
    
    # Get enrollment
    try:
        enrollment = Enrollment.objects.get(pk=id, student=user, is_active=True)
    except Enrollment.DoesNotExist:
        raise HttpError(404, "Enrollment not found")
    
    # Verify lesson exists
    try:
        lesson = Lesson.objects.get(pk=data.lesson_id, course=enrollment.course)
    except Lesson.DoesNotExist:
        raise HttpError(404, "Lesson not found")
    
    # Create or update progress
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson,
        defaults={
            'is_completed': data.completion_percentage >= 100,
            'completion_percentage': data.completion_percentage,
            'started_at': datetime.now()
        }
    )
    
    if not created:
        progress.completion_percentage = data.completion_percentage
        progress.is_completed = data.completion_percentage >= 100
        if data.completion_percentage >= 100 and not progress.completed_at:
            progress.completed_at = datetime.now()
        progress.save()
    
    # Update enrollment progress percentage
    total_lessons = enrollment.course.lessons.count()
    if total_lessons > 0:
        completed = enrollment.progress_records.filter(is_completed=True).count()
        enrollment.progress_percentage = int((completed / total_lessons) * 100)
        enrollment.save()
    
    return progress


# Register routers
api.add_router('/auth/', auth_router)
api.add_router('/courses', courses_router)
api.add_router('/enrollments', enrollments_router)


# Add datetime import
from datetime import datetime