# core/models.py

from django.db import models
from django.db.models import Avg, Count, OuterRef, Subquery # Add OuterRef, Subquery
from django.conf import settings # To link to the User model correctly
# from django.contrib.auth.models import User # Avoid importing User directly
from django.utils import timezone # For timestamp
from django.db.models import Avg, Count # Added Count # Import Avg for aggregatio
import os # Needed for path joining in helper
# Choices for Roles (if you want to add a role field to User later, or for logic)
# class Role(models.TextChoices):
#     ADMIN = 'ADMIN', 'Admin'
#     TEACHER = 'TEACHER', 'Teacher'
#     PARENT = 'PARENT', 'Parent'
#     STUDENT = 'STUDENT', 'Student' # If students need login

# --- SchoolClass Definition ---
class SchoolClass(models.Model):
    """Represents a class in the school, e.g., Grade 10A for 2024-2025."""
    name = models.CharField(max_length=100, help_text="e.g., Grade 10A, Kindergarten Blue")
    # Assuming you added this field back correctly
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025", default="N/A")
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_teacher_of',
        help_text="Optional: Primary teacher for this class (must be a user marked as teacher)"
    )

    # --- CLASS TERM/SUBJECT AVERAGE METHOD with DEBUGGING ---
    @property
    def term_subject_averages(self):
        """
        Calculates average scores for each subject within each term/exam name
        for students currently assigned to THIS class instance.
        Returns a nested dictionary:
        { 'Term Name': {'Subject Name': average_score, ...}, ... }
        """
        # --- Start Debug ---
        #print(f"\nDEBUG: Calculating term_subject_averages for Class PK={self.pk} ({self})")
        # --- End Debug ---

        # Get results only for students currently in this specific class
        # and only results that have a score.
        class_results_qs = Result.objects.filter(
            student__current_class=self, # Filter 1: Students must be in THIS class
            score__isnull=False          # Filter 2: Results must have a numerical score
        )

        # --- Debug ---
        #print(f"DEBUG:   Found {class_results_qs.count()} results with scores for students in this class.")
        # Optional: Print individual results found (can be long if many results)
        # for res in class_results_qs.select_related('student', 'subject'):
        #    print(f"DEBUG:     - Result: {res.student.full_name}, {res.subject.name}, {res.term_exam_name}, Score={res.score}")
        # --- End Debug ---

        term_data = class_results_qs.values(
            'term_exam_name', # Group by term
            'subject__name'   # Group by subject name within term
        ).annotate(
            average=Avg('score') # Calculate average for each group
        ).order_by(
            'term_exam_name', 'subject__name' # Optional ordering
        )

        # --- Debug ---
        # Convert QuerySet to list to evaluate it for printing
        term_data_list = list(term_data)
        #print(f"DEBUG:   Aggregated term_data: {term_data_list}")
        # --- End Debug ---

        # Structure the data into a nested dictionary
        averages_data = {}
        # Use term_data_list which is already evaluated
        for item in term_data_list:
            term = item['term_exam_name']
            subject = item['subject__name']
            # Check if 'average' key exists and is not None before rounding
            if item.get('average') is not None:
                 average = round(item['average'], 1)
            else:
                 average = None # Handle case where average might be None

            if average is not None:
                if term not in averages_data:
                    averages_data[term] = {}
                averages_data[term][subject] = average

        # --- Debug ---
        # print(f"DEBUG:   Final averages_data dictionary: {averages_data}")
        # --- End Debug ---

        return averages_data
    # --- END CLASS AVERAGE METHOD ---

    class Meta:
        verbose_name_plural = "School Classes"
        unique_together = ('name', 'academic_year')

    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class Subject(models.Model):
    """Represents a subject taught in the school."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class TeacherProfile(models.Model):
    """Extends the User model for Teachers."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        #primary_key=True,
        related_name='teacherprofile' # Allows user.teacherprofile access
    )
    phone_number = models.CharField(max_length=20, blank=True)
    # subjects_taught = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    # assigned_classes = models.ManyToManyField(SchoolClass, blank=True, related_name='teachers')
    # Note: Linking subjects/classes here might be too broad.
    # Often, teachers teach specific subjects *in* specific classes.
    # This complexity can be handled via the Result model or a dedicated Timetable model later.

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"

class ParentProfile(models.Model):
    """Extends the User model for Parents."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        #primary_key=True,
        related_name='parentprofile' # Allows user.parentprofile access
    )
    phone_number = models.CharField(max_length=20, blank=True)
    # The link to children is on the Student model via ManyToManyField

    def __str__(self):
        return f"Parent: {self.user.get_full_name() or self.user.username}"

# --- Helper function for student profile image paths ---
def student_profile_picture_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/student_profiles/<student_id>/<filename>
    # This helps keep files organized and avoids name collisions.
    _, file_extension = os.path.splitext(filename) # Get file extension
    # Use student ID for folder name. You could also use a UUID.
    # Optionally, rename filename to something consistent like 'profile.ext'
    # filename = f'profile{file_extension}'
    return f'student_profiles/{instance.id}/{filename}'
# --- End Helper Function ---

class Student(models.Model):
    """Represents a student."""
    student_id = models.CharField(max_length=20, unique=True, help_text="Unique school ID")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    current_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL, # Keep student record if class is deleted
        null=True,
        blank=False, # A student should ideally always have a class assigned
        related_name='students'
    )
    # Link to potentially multiple parent/guardian users
    parents = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True, # Can be added later
        related_name='children',
        help_text="Users associated as parents/guardians. Link existing users here."
        # Consider adding limit_choices_to={'parentprofile__isnull': False} in admin/forms later
    )
    # Optional: Link to a User account if students can log in
    # user_account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')

    # --- ADD PROFILE PICTURE FIELD ---
    profile_picture = models.ImageField(
        upload_to=student_profile_picture_path, # Use helper function for path
        null=True,  # Allow no picture
        blank=True, # Allow empty in forms/admin
        default=None, # Explicitly no default image in DB
        help_text="Optional: Student's profile picture."
    )
    # --- END PROFILE PICTURE FIELD ---

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    # --- ADD AVERAGE SCORE METHOD ---
    @property
    def average_score(self):
        """Calculates the average score across all recorded results with a numeric score."""
        # Filter results that have a non-null score and belong to this student
        results_with_scores = self.results.filter(score__isnull=False)
        if results_with_scores.exists():
            # Calculate the average using Django's aggregation
            average_data = results_with_scores.aggregate(Avg('score'))
            # 'average_data' will be a dictionary like {'score__avg': 85.5}
            # Round the average to a reasonable number of decimal places
            return round(average_data['score__avg'], 1) if average_data['score__avg'] is not None else None
        return None # Return None if no results with scores exist
    # --- END AVERAGE SCORE METHOD ---

    # --- ADD TERM AVERAGE METHOD ---
    @property
    def term_averages(self):
        """
        Calculates the average score for each term/exam name
        where at least one numeric score exists for that term.
        Returns a dictionary: {'Term Name': average_score, ...}
        """
        term_data = self.results.filter(
            score__isnull=False # Only consider results with scores
        ).values(
            'term_exam_name' # Group by term name
        ).annotate(
            average=Avg('score'), # Calculate average score for each group
            score_count=Count('score') # Count how many scores contributed
        ).order_by(
            'term_exam_name' # Optional: order terms alphabetically
        )

        # Format the result into a dictionary {term_name: rounded_average}
        averages_dict = {
            term['term_exam_name']: round(term['average'], 1)
            for term in term_data if term['average'] is not None
        }
        return averages_dict
    # --- END TERM AVERAGE METHOD ---

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

class Result(models.Model):
    """Represents a specific result/grade for a student in a subject."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results') # PROTECT might be better if subjects are critical
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL, # Record the class context at time of result
        null=True,
        blank=True, # Can be derived from student.current_class at time of entry
        related_name='results'
    )
    term_exam_name = models.CharField(max_length=100, help_text="e.g., Term 1, Midterm Exam, Final Project")
    score = models.FloatField(null=True, blank=True, help_text="Numerical score (e.g., 85.5)")
    grade = models.CharField(max_length=5, blank=True, help_text="Letter grade (e.g., A+, B-)") # Optional alternative/addition to score
    comments = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep result if teacher leaves
        null=True,
        blank=True, # May be entered by admin, or system generated
        related_name='results_recorded'
    )
    date_recorded = models.DateTimeField(auto_now_add=True) # Automatically set when created
    last_updated = models.DateTimeField(auto_now=True) # Automatically updates on save

    class Meta:
        # Prevent duplicate results for the same student, subject, and term/exam
        unique_together = ('student', 'subject', 'term_exam_name')
        ordering = ['-date_recorded'] # Show newest results first by default

    def __str__(self):
        display_mark = self.grade if self.grade else str(self.score)
        return f"{self.student} - {self.subject} ({self.term_exam_name}): {display_mark}"

class Announcement(models.Model):
    """Represents a site-wide or role-specific announcement."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep announcement if user is deleted
        null=True,
        related_name='announcements_posted'
    )
    timestamp = models.DateTimeField(default=timezone.now)
    # Optional: Target specific roles (can be simplified initially)
    # VISIBILITY_CHOICES = [
    #     ('ALL', 'All Users'),
    #     ('PARENTS', 'Parents Only'),
    #     ('TEACHERS', 'Teachers Only'),
    #     ('STAFF', 'Staff Only'),
    # ]
    # visible_to = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='ALL')

    class Meta:
        ordering = ['-timestamp'] # Show newest first

    def __str__(self):
        return self.title

class AttendanceRecord(models.Model):
    """Records attendance status for a student on a specific date."""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused Absence'), # Added another common option
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(default=timezone.now) # Use DateField for just the date
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow admin entries or system generation later
        related_name='attendance_recorded'
    )
    # Optional: Link to the class context when attendance was taken
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, help_text="Optional notes (e.g., reason for absence/lateness)")
    timestamp = models.DateTimeField(auto_now_add=True) # When the record was created/updated

    class Meta:
        # Prevent multiple attendance records for the same student on the same date
        unique_together = ('student', 'date')
        ordering = ['-date', 'student__last_name'] # Order by date then student name

    def __str__(self):
        return f"{self.student.full_name} - {self.date}: {self.get_status_display()}"



def carousel_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/carousel_images/<filename>
    # Important: Avoid filename collisions if multiple users upload same name
    # You might want to add a unique ID or timestamp to filename
    return f'carousel_images/{filename}'

class CarouselImage(models.Model):
    title = models.CharField(max_length=100, help_text="Optional title/description for the image (e.g., 'Sports Day')")
    image = models.ImageField(upload_to=carousel_image_path) # Use ImageField
    caption = models.CharField(max_length=200, blank=True, help_text="Optional caption overlay")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide this image from the carousel")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'title'] # Order by specified order, then title

    def __str__(self):
        return self.title or f"Carousel Image {self.id}"


# --- Helper function for image paths ---
def news_image_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/news_images/<news_article_id>/<filename>
    return f'news_images/{instance.article.id}/{filename}'

# --- News Article Model ---
class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateField(default=timezone.now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True, # Optional author
        related_name='news_articles_authored'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date', '-created_at'] # Show newest first

    def __str__(self):
        return self.title

# --- News Image Model (Related to NewsArticle) ---
class NewsImage(models.Model):
    article = models.ForeignKey(
        NewsArticle,
        on_delete=models.CASCADE, # Delete images if article is deleted
        related_name='images' # Allows article.images.all() access
    )
    image = models.ImageField(upload_to=news_image_path)
    caption = models.CharField(max_length=255, blank=True, help_text="Optional caption for this image")
    order = models.PositiveIntegerField(default=0, help_text="Display order within the article")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.article.title}" + (f" ({self.caption})" if self.caption else "")