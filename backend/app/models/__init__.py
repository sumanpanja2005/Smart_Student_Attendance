"""
Database collection models architecture specification.

Future collections to be managed in MongoDB:
- `users`: Role-based authentication & user accounts (Admin, Teacher, Student)
- `students`: Student profiles, roll numbers, department, semester, class associations
- `teachers`: Teacher profiles, department, assigned subjects & classes
- `subjects`: Course modules, subject codes, credit details
- `classes`: Academic schedules, timetable allocations, room numbers
- `attendance`: Attendance session logs, timestamped student status records
- `face_embeddings`: Registered facial embedding vectors associated with student IDs
- `notifications`: Alerts, warning notifications, low-attendance warnings
"""

COLLECTIONS = [
    "users",
    "students",
    "teachers",
    "subjects",
    "classes",
    "attendance",
    "face_embeddings",
    "notifications",
]
