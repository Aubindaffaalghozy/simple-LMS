"""
Role-Based Access Control (RBAC) decorators for Simple LMS API
"""
from functools import wraps
from typing import Callable, List
from ninja.errors import HttpError
from django.contrib.auth.models import User
from courses.models import Enrollment


def get_user_role(user: User, course_id: int = None) -> str:
    """Get user's role in a specific course."""
    if course_id:
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course_id=course_id,
                is_active=True
            )
            return enrollment.role
        except Enrollment.DoesNotExist:
            return 'none'
    
    # Check if user is an instructor (has taught courses)
    if hasattr(user, 'taught_courses') and user.taught_courses.exists():
        return 'instructor'
    
    return 'student'


def is_instructor(user: User, course_id: int = None) -> bool:
    """Check if user is an instructor for a course."""
    if course_id:
        role = get_user_role(user, course_id)
        return role in ['instructor', 'assistant']
    return user.taught_courses.exists()


def is_admin(user: User) -> bool:
    """Check if user is a superuser or staff."""
    return user.is_superuser or user.is_staff


def is_student(user: User, course_id: int = None) -> bool:
    """Check if user is a student for a course."""
    if course_id:
        role = get_user_role(user, course_id)
        return role == 'student'
    return True


def is_enrolled(user: User, course_id: int) -> bool:
    """Check if user is enrolled in a course."""
    return Enrollment.objects.filter(
        student=user,
        course_id=course_id,
        is_active=True
    ).exists()


def is_course_owner(user: User, course) -> bool:
    """Check if user is the owner (instructor) of a course."""
    return course.instructor_id == user.id


# ==================== Decorators ====================

def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        return func(request, *args, **kwargs)
    return wrapper


def is_instructor_decorator(func: Callable) -> Callable:
    """Decorator to require instructor role."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        
        user = request.auth
        if not is_instructor(user):
            raise HttpError(403, "Instructor role required")
        
        return func(request, *args, **kwargs)
    return wrapper


def is_admin_decorator(func: Callable) -> Callable:
    """Decorator to require admin role."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        
        user = request.auth
        if not is_admin(user):
            raise HttpError(403, "Admin role required")
        
        return func(request, *args, **kwargs)
    return wrapper


def is_student_decorator(func: Callable) -> Callable:
    """Decorator to require student role."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        
        user = request.auth
        if not is_student(user):
            raise HttpError(403, "Student role required")
        
        return func(request, *args, **kwargs)
    return wrapper


def require_course_enrollment(func: Callable) -> Callable:
    """Decorator to require enrollment in a course."""
    @wraps(func)
    def wrapper(request, course_id: int, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        
        user = request.auth
        if not is_enrolled(user, course_id):
            raise HttpError(403, "Enrollment required")
        
        return func(request, course_id, *args, **kwargs)
    return wrapper


def require_course_ownership(func: Callable) -> Callable:
    """Decorator to require course ownership."""
    @wraps(func)
    def wrapper(request, course_id: int, *args, **kwargs):
        if not hasattr(request, 'auth') or request.auth is None:
            raise HttpError(401, "Authentication required")
        
        user = request.auth
        from courses.models import Course
        
        try:
            course = Course.objects.get(pk=course_id)
            if not is_course_owner(user, course) and not is_admin(user):
                raise HttpError(403, "Course ownership required")
        except Course.DoesNotExist:
            raise HttpError(404, "Course not found")
        
        return func(request, course_id, *args, **kwargs)
    return wrapper