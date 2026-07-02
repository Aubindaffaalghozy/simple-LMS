from config.celery import app


@app.task
def send_enrollment_email(enrollment_id: int) -> str:
    return f"Enrollment email queued for {enrollment_id}"


@app.task
def generate_certificate(enrollment_id: int) -> str:
    return f"Certificate generation queued for {enrollment_id}"


@app.task
def update_course_statistics() -> str:
    return "Course statistics update queued"


@app.task
def export_course_report(course_id: int) -> str:
    return f"Course report export queued for {course_id}"
