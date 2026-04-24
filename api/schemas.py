"""
API Schemas for Simple LMS
Pydantic models for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ==================== User Schemas ====================

class UserOut(BaseModel):
    """Schema for user data in responses."""
    id: int
    username: str
    first_name: str
    last_name: str
    email: str

    class Config:
        from_attributes = True


class UserProfileOut(BaseModel):
    """Extended user profile with additional info."""
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    date_joined: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


# ==================== Auth Schemas ====================

class RegisterIn(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)


class LoginIn(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class TokenOut(BaseModel):
    """Schema for JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class TokenRefreshIn(BaseModel):
    """Schema for refreshing tokens."""
    refresh_token: str


# ==================== Course Schemas ====================

class CategoryOut(BaseModel):
    """Schema for category in responses."""
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class CourseIn(BaseModel):
    """Schema for creating/updating a course."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default='-')
    category_id: int
    price: int = Field(default=0, ge=0)
    is_published: bool = Field(default=False)
    max_students: int = Field(default=100, ge=1)


class CourseOut(BaseModel):
    """Schema for course in list responses."""
    id: int
    name: str
    description: str
    price: int
    image: Optional[str] = None
    is_published: bool
    max_students: int
    instructor: UserOut
    category: CategoryOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        
    @field_validator('image', mode='before')
    @classmethod
    def convert_image(cls, v):
        if v is None:
            return None
        return str(v) if hasattr(v, '__str__') else v


class CourseDetailOut(CourseOut):
    """Extended course detail with enrollment count."""
    enrolled_count: int = 0

    class Config:
        from_attributes = True


# ==================== Enrollment Schemas ====================

class EnrollmentIn(BaseModel):
    """Schema for enrolling in a course."""
    course_id: int


class EnrollmentOut(BaseModel):
    """Schema for enrollment in responses."""
    id: int
    course: CourseOut
    student: UserOut
    role: str
    enrolled_at: datetime
    is_active: bool
    progress_percentage: int

    class Config:
        from_attributes = True


class EnrollmentListOut(BaseModel):
    """Simplified enrollment for list."""
    id: int
    course_id: int
    course_name: str
    role: str
    enrolled_at: datetime
    progress_percentage: int

    class Config:
        from_attributes = True


class ProgressIn(BaseModel):
    """Schema for marking progress."""
    lesson_id: int
    completion_percentage: int = Field(default=100, ge=0, le=100)


class ProgressOut(BaseModel):
    """Schema for progress in responses."""
    id: int
    lesson_id: int
    is_completed: bool
    completion_percentage: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== Pagination ====================

class PaginatedCoursesOut(BaseModel):
    """Paginated course list response."""
    items: List[CourseOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedEnrollmentsOut(BaseModel):
    """Paginated enrollment list response."""
    items: List[EnrollmentListOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Error Schemas ====================

class ErrorOut(BaseModel):
    """Schema for error responses."""
    detail: str


class ValidationErrorOut(BaseModel):
    """Schema for validation errors."""
    detail: List[dict]