from ninja import FilterSchema, Field, Query
from typing import Optional, List
from datetime import datetime
from django.db.models import Q


class CourseFilter(FilterSchema):
    # Filter sederhana: exact match
    price: Optional[int] = 0

    # Filter berdasarkan tanggal
    created_at: Optional[datetime] = None

    # Search di beberapa field sekaligus
    search: Optional[str] = Field(
        None,
        q=['name__icontains', 'description__icontains']
    )

    def filter_price(self, value: int) -> Q:
        """Custom filter: menampilkan course dengan harga di atas value."""
        return Q(price__gt=value)

    def filter_created_at(self, value: datetime) -> Q:
        """Custom filter: menampilkan course yang dibuat setelah tanggal tertentu."""
        if value:
            return Q(created_at__gt=value)
        return Q()