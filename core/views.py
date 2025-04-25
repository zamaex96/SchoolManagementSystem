# core/views.py
from django.shortcuts import render, redirect, get_object_or_404 # Add get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages # To show success messages
from django.utils.dateparse import parse_date # To handle date input
from django.db import transaction # For atomic saving
from django.utils import timezone
from datetime import timedelta # For date calculations
from django.db.models import Count, Q # For counting attendance statuses
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Student, Result, ParentProfile, TeacherProfile, SchoolClass, Announcement, AttendanceRecord, NewsArticle, NewsImage # Add Result
from .forms import ResultForm # Import the new form
import csv # Standard Python library for CSV handling
from django.http import HttpResponse # To return the CSV file
from .models import CarouselImage # Import

# Homepage view
def home(request):
    announcement_list = Announcement.objects.all()  # Get all, order is handled by model Meta
    paginator = Paginator(announcement_list, 3)  # Show 3 announcements per page

    page_number = request.GET.get('page')
    try:
        announcements = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        announcements = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        announcements = paginator.page(paginator.num_pages)

    # Fetch active carousel images ordered correctly
    carousel_images = CarouselImage.objects.filter(is_active=True).order_by('order')

    context = {'page_title': 'Homepage', 'announcements': announcements, 'carousel_images': carousel_images}
    return render(request, 'home.html', context) # Assumes templates/home.html exists

# Parent dashboard view
@login_required
def parent_dashboard(request):
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        # Not a parent, redirect home
        return redirect('home')

    children = request.user.children.all().prefetch_related('results', 'results__subject', 'current_class')

    # --- Calculate Attendance Summaries ---
    # Define time window (e.g., last 14 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=14)

    attendance_summary = {}
    for child in children:
        summary = AttendanceRecord.objects.filter(
            student=child,
            date__range=[start_date, end_date]  # Filter by date range
        ).aggregate(
            absent_count=Count('pk', filter=Q(status='ABSENT')),  # Count absences
            late_count=Count('pk', filter=Q(status='LATE'))  # Count lates
        )
        attendance_summary[child.id] = summary
    # --- End Attendance Summaries ---

    # --- Paginate Announcements ---
    announcement_list = Announcement.objects.all()
    paginator = Paginator(announcement_list, 5) # Show 5 per page on dashboards
    page_number = request.GET.get('page')
    try:
        announcements = paginator.page(page_number)
    except PageNotAnInteger:
        announcements = paginator.page(1)
    except EmptyPage:
        announcements = paginator.page(paginator.num_pages)
    # --- End Pagination ---

    context = {
        'parent': request.user,
        'children_with_results': children,
        'announcements': announcements,
        'attendance_summary': attendance_summary,  # Add summary to context
        'attendance_period_days': 14,  # Pass period to template
        'page_title': 'Parent Dashboard'
    }
    return render(request, 'core/parent_dashboard.html', context) # Assumes templates/core/parent_dashboard.html exists

@login_required
def teacher_dashboard(request):
    # Check if the logged-in user is a teacher
    try:
        teacher_profile = request.user.teacherprofile
    except TeacherProfile.DoesNotExist:
        # Not a teacher, redirect home
        return redirect('home')

    # Find classes where this user is the class_teacher
    # Remember related_name='class_teacher_of' on SchoolClass.class_teacher?
    assigned_classes = request.user.class_teacher_of.all().prefetch_related('students')
    # Prefetch students to optimize DB queries

    # --- Get Today's Attendance Summary for Assigned Classes ---
    today = timezone.now().date()
    attendance_today = {}
    for sc in assigned_classes:
        summary = AttendanceRecord.objects.filter(
            school_class=sc,
            date=today
        ).aggregate(
            present_count=Count('pk', filter=Q(status='PRESENT')),
            absent_count=Count('pk', filter=Q(status='ABSENT')),
            late_count=Count('pk', filter=Q(status='LATE')),
            excused_count=Count('pk', filter=Q(status='EXCUSED'))
        )
        total_students = sc.students.count()  # Get total students in class
        summary['total_students'] = total_students
        summary['not_recorded'] = total_students - (
                    summary['present_count'] + summary['absent_count'] + summary['late_count'] + summary[
                'excused_count'])
        attendance_today[sc.id] = summary
    # --- End Today's Summary ---

    # Optional: Gather all students from those classes
    # students_in_classes = Student.objects.filter(current_class__in=assigned_classes).order_by('last_name', 'first_name')

    # --- Paginate Announcements ---
    announcement_list = Announcement.objects.all()
    paginator = Paginator(announcement_list, 5) # Show 5 per page
    page_number = request.GET.get('page')
    try:
        announcements = paginator.page(page_number)
    except PageNotAnInteger:
        announcements = paginator.page(1)
    except EmptyPage:
        announcements = paginator.page(paginator.num_pages)
    # --- End Pagination ---

    context = {
        'teacher': request.user,
        'assigned_classes': assigned_classes, # Pass the classes queryset
        # 'students_in_classes': students_in_classes, # Alternative/additional way to pass students
        'attendance_today': attendance_today,  # Add today's summary
        'announcements': announcements,
        'page_title': 'Teacher Dashboard'
    }
    return render(request, 'core/teacher_dashboard.html', context)

@login_required
def add_edit_result(request, student_id=None, result_id=None):
    """
    - If `result_id` is provided, we’re editing; fetch that Result and its student.
    - Otherwise we’re adding; fetch the Student by student_id.
    """
    if result_id:
        result = get_object_or_404(Result, id=result_id)
        student = result.student
    else:
        result = None
        student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = ResultForm(request.POST, instance=result)
        if form.is_valid():
            r = form.save(commit=False)
            r.student      = student
            r.recorded_by  = request.user
            r.school_class = student.current_class
            r.save()
            return redirect('teacher_dashboard')
    else:
        form = ResultForm(instance=result)

    return render(request, 'core/add_edit_result.html', {
        'form': form,
        'student': student,
        'result':  result,
        'page_title': 'Edit Result' if result else 'Add New Result',
    })

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'parentprofile'):
        return redirect('parent_dashboard')
    elif hasattr(request.user, 'teacherprofile'):
        return redirect('teacher_dashboard')
    elif request.user.is_staff: # Or is_superuser
        # Redirect staff/admin to the Django admin index
        return redirect('admin:index') # Use admin namespace
    else:
        # Default fallback - maybe user has no role yet?
        messages.info(request, "Your account role is not yet configured.")
        return redirect('home') # Or a specific "pending" page


@login_required
def delete_result(request, result_id):
    # Get the result object or return 404
    result = get_object_or_404(Result, pk=result_id)
    student_name = result.student.full_name # Get student name for messages before deleting

    # --- Permission Check ---
    # Allow deletion only by staff or the teacher assigned to the student's current class
    is_authorized = False
    if request.user.is_staff:
        is_authorized = True
    else:
        try:
            teacher_profile = request.user.teacherprofile
            # Check if teacher is assigned to the student's current class
            if result.student.current_class in request.user.class_teacher_of.all():
                 is_authorized = True
            # Optional: Add check if teacher recorded this specific result?
            # elif result.recorded_by == request.user:
            #     is_authorized = True
        except TeacherProfile.DoesNotExist:
            pass # User is not a teacher

    if not is_authorized:
        messages.error(request, "You do not have permission to delete this result.")
        return redirect('teacher_dashboard') # Or wherever appropriate

    if request.method == 'POST':
        # User confirmed deletion via the form
        result.delete()
        messages.success(request, f"Result for {student_name} ({result.subject.name} - {result.term_exam_name}) deleted successfully.")
        return redirect('teacher_dashboard') # Redirect back after deletion
    else:
        # GET request: Show the confirmation page
        context = {
            'result': result,
            'page_title': 'Confirm Result Deletion'
        }
        return render(request, 'core/result_delete_confirm.html', context)


@login_required
def student_profile(request, student_id):
    student = get_object_or_404(Student.objects.prefetch_related('parents'), pk=student_id) # Prefetch parents

    # --- Authorization Check ---
    is_authorized = False
    user = request.user

    if user.is_staff: # Staff can see any profile
        is_authorized = True
    elif hasattr(user, 'parentprofile'): # Check if user is a parent
        # Check if this user is listed as one of the student's parents
        if user in student.parents.all():
            is_authorized = True
    elif hasattr(user, 'teacherprofile'): # Check if user is a teacher
        # Check if teacher is assigned to the student's current class
        if student.current_class in user.class_teacher_of.all():
            is_authorized = True
        # Optional: Add other checks, e.g., if teacher recorded results for this student?
        # elif Result.objects.filter(student=student, recorded_by=user).exists():
        #     is_authorized = True

    if not is_authorized:
        # Option 1: Show generic 404 (less informative but hides info)
        # raise Http404("Student profile not found or permission denied.")
        # Option 2: Redirect with message (more user-friendly)
        messages.error(request, "You do not have permission to view this student's profile.")
        # Redirect to their own dashboard or home
        if hasattr(user, 'parentprofile'):
            return redirect('parent_dashboard')
        elif hasattr(user, 'teacherprofile'):
            return redirect('teacher_dashboard')
        else:
            return redirect('home')

    # Get results separately if needed, or assume they are handled elsewhere
    # student_results = student.results.all().order_by('-date_recorded')

    # --- Handle Date Range Filtering for Attendance ---
    default_end_date = timezone.now().date()
    default_start_date = default_end_date - timedelta(days=30) # Default to last 30 days

    # Get dates from GET request, use defaults if not provided or invalid
    start_date_str = request.GET.get('start_date', default_start_date.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', default_end_date.strftime('%Y-%m-%d'))

    start_date = parse_date(start_date_str) or default_start_date
    end_date = parse_date(end_date_str) or default_end_date

    # Ensure start_date is not after end_date
    if start_date > end_date:
        start_date = end_date - timedelta(days=30) # Reset to 30 days before end date

    # --- Fetch Filtered Attendance Records ---
    attendance_records = student.attendance_records.filter(
        date__range=[start_date, end_date]
    ).order_by('-date') # Order most recent first within the range

    # --- Calculate Summary for the Filtered Range ---
    attendance_summary = attendance_records.aggregate(
        present_count=Count('pk', filter=Q(status='PRESENT')),
        absent_count=Count('pk', filter=Q(status='ABSENT')),
        late_count=Count('pk', filter=Q(status='LATE')),
        excused_count=Count('pk', filter=Q(status='EXCUSED'))
    )
    # --- End Attendance Fetching/Summary ---

    context = {
        'student': student,
        # 'results': student_results, # Could pass results here too if desired
        'attendance_records': attendance_records, # Pass filtered records
        'attendance_summary': attendance_summary, # Pass summary for the range
        'start_date': start_date, # Pass dates back for form pre-filling
        'end_date': end_date,
        'start_date_str': start_date.strftime('%Y-%m-%d'), # Pass string versions too
        'end_date_str': end_date.strftime('%Y-%m-%d'),
        'page_title': f"Profile: {student.full_name}",
    }
    return render(request, 'core/student_profile.html', context)

@login_required
def take_attendance(request, class_id):
    # Ensure user is a teacher and assigned to this class
    try:
        teacher_profile = request.user.teacherprofile
    except TeacherProfile.DoesNotExist:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    school_class = get_object_or_404(SchoolClass, pk=class_id)

    if school_class not in request.user.class_teacher_of.all():
        messages.error(request, f"You are not assigned to class {school_class}.")
        return redirect('teacher_dashboard')

    # Get students in this class
    students = Student.objects.filter(current_class=school_class).order_by('last_name', 'first_name')

    # Handle date selection - default to today
    attendance_date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    attendance_date = parse_date(attendance_date_str)
    if not attendance_date:
        attendance_date = timezone.now().date() # Fallback to today if parse fails
        attendance_date_str = attendance_date.strftime('%Y-%m-%d')

    # Get existing records for this class & date to pre-fill form
    existing_records = AttendanceRecord.objects.filter(
        school_class=school_class,
        date=attendance_date
    ).values('student_id', 'status', 'notes') # Get relevant data efficiently

    existing_status = {record['student_id']: {'status': record['status'], 'notes': record['notes']} for record in existing_records}

    if request.method == 'POST':
        try:
            # Use atomic transaction to save all records or none
            with transaction.atomic():
                records_to_update = []
                records_to_create = []
                for student in students:
                    status = request.POST.get(f'status_{student.id}')
                    notes = request.POST.get(f'notes_{student.id}', '') # Get notes, default to empty string

                    if status: # Only process if a status was submitted for the student
                        record_data = {
                            'student': student,
                            'date': attendance_date,
                            'status': status,
                            'notes': notes,
                            'recorded_by': request.user,
                            'school_class': school_class
                        }

                        # Check if record exists to update or create
                        existing = existing_status.get(student.id)
                        if existing:
                            # Update existing record only if status or notes changed
                            if existing['status'] != status or existing['notes'] != notes:
                                record_to_update = AttendanceRecord.objects.get(student=student, date=attendance_date)
                                record_to_update.status = status
                                record_to_update.notes = notes
                                record_to_update.recorded_by = request.user # Update recorder
                                records_to_update.append(record_to_update)
                        else:
                            # Create new record instance
                            records_to_create.append(AttendanceRecord(**record_data))

                # Bulk update existing records that changed
                if records_to_update:
                    AttendanceRecord.objects.bulk_update(records_to_update, ['status', 'notes', 'recorded_by'])

                # Bulk create new records
                if records_to_create:
                    AttendanceRecord.objects.bulk_create(records_to_create)

            messages.success(request, f"Attendance for {school_class} on {attendance_date.strftime('%Y-%m-%d')} saved successfully.")
            return redirect('teacher_dashboard') # Redirect back after saving
        except Exception as e:
             messages.error(request, f"An error occurred while saving attendance: {e}")


    # Prepare initial data for the template (pre-fill from existing records)
    attendance_data = {}
    for student in students:
        attendance_data[student.id] = existing_status.get(student.id, {'status': 'PRESENT', 'notes': ''}) # Default to Present

    context = {
        'school_class': school_class,
        'students': students,
        'attendance_date': attendance_date,
        'attendance_date_str': attendance_date_str, # For the date input value
        'attendance_data': attendance_data, # Pass existing/default data
        'status_choices': AttendanceRecord.STATUS_CHOICES,
        'page_title': f'Take Attendance for {school_class}'
    }
    return render(request, 'core/take_attendance_form.html', context)

@login_required
def view_class_attendance(request, class_id):
    # --- Permission Checks ---
    try:
        teacher_profile = request.user.teacherprofile
    except TeacherProfile.DoesNotExist:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    school_class = get_object_or_404(SchoolClass, pk=class_id)

    if school_class not in request.user.class_teacher_of.all():
        messages.error(request, f"You are not assigned to class {school_class}.")
        return redirect('teacher_dashboard')

    # --- Handle Date Range Filtering ---
    # Default to just 'today' for this view initially, but allow range selection
    default_date = timezone.now().date()
    start_date_str = request.GET.get('start_date', default_date.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', default_date.strftime('%Y-%m-%d')) # Default end to same as start

    start_date = parse_date(start_date_str) or default_date
    end_date = parse_date(end_date_str) or start_date # Default end to start date if invalid

    if start_date > end_date: # Ensure valid range
        start_date = end_date

    # --- Fetch Attendance Records for the Class within the range ---
    attendance_records = AttendanceRecord.objects.filter(
        school_class=school_class,
        date__range=[start_date, end_date]
    ).select_related( # Optimize by fetching related student in one go
        'student'
    ).order_by('-date', 'student__last_name', 'student__first_name')

    # --- Calculate Summary for the Period (Optional but nice) ---
    attendance_summary = attendance_records.aggregate(
        present_count=Count('pk', filter=Q(status='PRESENT')),
        absent_count=Count('pk', filter=Q(status='ABSENT')),
        late_count=Count('pk', filter=Q(status='LATE')),
        excused_count=Count('pk', filter=Q(status='EXCUSED'))
    )

    context = {
        'school_class': school_class,
        'attendance_records': attendance_records,
        'attendance_summary': attendance_summary,
        'start_date': start_date,
        'end_date': end_date,
        'start_date_str': start_date.strftime('%Y-%m-%d'),
        'end_date_str': end_date.strftime('%Y-%m-%d'),
        'page_title': f'View Attendance: {school_class}'
    }
    return render(request, 'core/view_class_attendance.html', context)

@login_required
def export_class_results_csv(request, class_id):
    # --- Permission Check ---
    # Ensure user is staff or the assigned teacher for this class
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    is_authorized = False
    if request.user.is_staff:
        is_authorized = True
    elif hasattr(request.user, 'teacherprofile'):
        if school_class in request.user.class_teacher_of.all():
            is_authorized = True

    if not is_authorized:
        messages.error(request, f"You do not have permission to export results for {school_class}.")
        # Redirect based on role
        if hasattr(request.user, 'teacherprofile'):
            return redirect('teacher_dashboard')
        elif request.user.is_staff:
             # Admins could perhaps be redirected to the admin page for the class?
             # return redirect('admin:core_schoolclass_changelist') # Example
             return redirect('admin:index')
        else:
            return redirect('home')

    # --- Prepare CSV Response ---
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="results_{school_class.name}_{school_class.academic_year}.csv"'},
    )

    writer = csv.writer(response)
    # Write Header Row
    writer.writerow([
        'Student ID', 'Student Name', 'Subject', 'Term/Exam',
        'Score', 'Grade', 'Comments', 'Date Recorded', 'Recorded By'
    ])

    # --- Get Data ---
    # Get all students currently in the class
    students_in_class = Student.objects.filter(current_class=school_class)
    # Get all results for those students, ordered nicely
    results = Result.objects.filter(
        student__in=students_in_class
    ).select_related( # Optimize related lookups
        'student', 'subject', 'recorded_by'
    ).order_by(
        'student__last_name', 'student__first_name', 'subject__name', 'term_exam_name'
    )

    # --- Write Data Rows ---
    for result in results:
        writer.writerow([
            result.student.student_id,
            result.student.full_name,
            result.subject.name,
            result.term_exam_name,
            result.score,
            result.grade,
            result.comments,
            result.date_recorded.strftime('%Y-%m-%d %H:%M') if result.date_recorded else '', # Format date
            result.recorded_by.username if result.recorded_by else 'N/A'
        ])

    return response

@login_required
def export_parent_results_csv(request):
    # --- Permission Check ---
    # Ensure user is a parent
    try:
        parent_profile = request.user.parentprofile
    except ParentProfile.DoesNotExist:
        messages.error(request, "You must be logged in as a parent to export results.")
        return redirect('home') # Or dashboard redirect

    # --- Get Parent's Children ---
    children = request.user.children.all() # Get all children linked to this parent user
    if not children.exists():
        messages.info(request, "No children found associated with your account.")
        return redirect('parent_dashboard') # Redirect back if no children

    # --- Prepare CSV Response ---
    # Create a filename (can be generic or include parent username)
    parent_name = request.user.username
    filename = f"results_children_of_{parent_name}.csv"
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)
    # Write Header Row
    writer.writerow([
        'Child Name', 'Child Student ID', 'Class', 'Subject', 'Term/Exam',
        'Score', 'Grade', 'Comments', 'Date Recorded'
    ])

    # --- Get Data ---
    # Get all results for ALL children of this parent
    results = Result.objects.filter(
        student__in=children # Filter results for the parent's children
    ).select_related(
        'student', 'subject', 'school_class' # Optimize related lookups
    ).order_by(
        'student__last_name', 'student__first_name', 'subject__name', 'term_exam_name'
    )

    # --- Write Data Rows ---
    for result in results:
        writer.writerow([
            result.student.full_name,
            result.student.student_id,
            result.school_class.name if result.school_class else 'N/A', # Handle potential null class
            result.subject.name,
            result.term_exam_name,
            result.score,
            result.grade,
            result.comments,
            result.date_recorded.strftime('%Y-%m-%d %H:%M') if result.date_recorded else '',
        ])

    return response

# --- View for the News Listing Page ---
def news_list(request):
    news_article_list = NewsArticle.objects.all().prefetch_related('images') # Prefetch images

    # Optional Pagination for news list
    paginator = Paginator(news_article_list, 5) # Show 5 articles per page
    page_number = request.GET.get('page')
    try:
        news_articles = paginator.page(page_number)
    except PageNotAnInteger:
        news_articles = paginator.page(1)
    except EmptyPage:
        news_articles = paginator.page(paginator.num_pages)

    context = {
        'news_articles': news_articles, # Pass paginated articles
        'page_title': 'School News'
    }
    # Use a Django template, not a static file
    return render(request, 'core/news_list.html', context)

# --- Optional: View for a Single News Article Detail ---
# def news_detail(request, article_id):
#     article = get_object_or_404(NewsArticle.objects.prefetch_related('images'), pk=article_id)
#     context = {'article': article, 'page_title': article.title}
#     return render(request, 'core/news_detail.html', context)

def news_detail(request, article_id):
    # Prefetch images when getting the single article
    article = get_object_or_404(NewsArticle.objects.prefetch_related('images'), pk=article_id)
    context = {
        'article': article,
        'page_title': article.title  # Use article title for page title
    }
    return render(request, 'core/news_detail.html', context)