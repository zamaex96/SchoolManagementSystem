# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import admin, messages # Add messages
from django.shortcuts import render # Add render
from django.http import HttpResponseRedirect # Add redirect
from .models import SchoolClass, Subject, TeacherProfile, ParentProfile, Student, Result, Announcement, AttendanceRecord, NewsArticle, NewsImage
from import_export.admin import ImportExportModelAdmin # Import
from .forms import AssignClassForm
from .models import CarouselImage # Import the new model
# --- Inline Admin for Profiles (to show on User page) ---

class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    fk_name = 'user'

class ParentProfileInline(admin.StackedInline):
    model = ParentProfile
    can_delete = False
    verbose_name_plural = 'Parent Profile'
    fk_name = 'user'

# --- PASTE THIS RoleFilter CLASS DEFINITION HERE (if missing) ---
class RoleFilter(admin.SimpleListFilter):
    title = 'role'  # Title displayed in the admin sidebar
    parameter_name = 'role' # Parameter used in the URL query

    def lookups(self, request, model_admin):
        return (
            ('teacher', 'Teachers'),
            ('parent', 'Parents'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'teacher':
            return queryset.filter(teacherprofile__isnull=False)
        if self.value() == 'parent':
            return queryset.filter(parentprofile__isnull=False)
        return queryset
# --- END OF RoleFilter DEFINITION ---

# --- Custom User Admin ---

class CustomUserAdmin(BaseUserAdmin):
    inlines = (TeacherProfileInline, ParentProfileInline) # Add profiles here

    # Optional: Add profile existence to list display
    def is_teacher(self, obj):
        return hasattr(obj, 'teacherprofile')
    is_teacher.boolean = True

    def is_parent(self, obj):
        return hasattr(obj, 'parentprofile')
    is_parent.boolean = True

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_teacher', 'is_parent')
    list_filter = BaseUserAdmin.list_filter + (RoleFilter,)

# Re-register User admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# --- ModelAdmin for Your App's Models ---

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'class_teacher')
    search_fields = ('name', 'academic_year', 'class_teacher__username', 'class_teacher__first_name', 'class_teacher__last_name')
    list_filter = ('academic_year',)
    autocomplete_fields = ['class_teacher'] # Makes selecting teacher easier if many users

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'current_class', 'display_parents')
    search_fields = ('student_id', 'first_name', 'last_name', 'current_class__name', 'parents__username')
    list_filter = ('current_class__academic_year', 'current_class__name')
    autocomplete_fields = ['current_class', 'parents'] # Easier selection
    # --- ADD ADMIN ACTIONS ---
    actions = ['assign_to_class']
    # --- END ADMIN ACTIONS ---

    # --- Use fieldsets for better layout on change form ---
    fieldsets = (
        ('Personal Information', {
            'fields': ('student_id', 'first_name', 'last_name', 'date_of_birth', 'profile_picture') # Add profile_picture here
        }),
        ('Academic Information', {
            'fields': ('current_class',)
        }),
        ('Family Information', {
            'fields': ('parents',)
        }),
    )
    # --- End fieldsets ---


    def display_parents(self, obj):
        return ", ".join([parent.get_full_name() or parent.username for parent in obj.parents.all()])
    display_parents.short_description = 'Parents/Guardians'

    # --- DEFINE THE ACTION FUNCTION ---
    @admin.action(description='Assign selected students to a class')
    def assign_to_class(self, request, queryset):
        # Handle the POST request from the intermediate page
        if 'apply' in request.POST:
            form = AssignClassForm(request.POST)
            if form.is_valid():
                school_class = form.cleaned_data['school_class']
                # Update selected students
                updated_count = queryset.update(current_class=school_class)
                # Display success message
                self.message_user(request,
                                  f"Successfully assigned {updated_count} students to class {school_class}.",
                                  messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path()) # Redirect back to the changelist
            else:
                 # If form is invalid (shouldn't happen with just ModelChoiceField unless nothing selected)
                 self.message_user(request, "Invalid class selection.", messages.ERROR)

        # If not POSTing back or form invalid, show the intermediate page
        form = AssignClassForm()
        context = {
            'title': "Assign Students to Class",
            'queryset': queryset,
            'form': form,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME # Needed for template
        }
        # Render an intermediate page (we need to create this template)
        return render(request, 'admin/core/student/assign_class_intermediate.html', context)
    # --- END ACTION FUNCTION ---

@admin.register(Result)
class ResultAdmin(ImportExportModelAdmin):
    list_display = ('student', 'subject', 'term_exam_name', 'score', 'grade', 'date_recorded', 'recorded_by')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id', 'subject__name', 'term_exam_name')
    list_filter = ('subject', 'term_exam_name', 'date_recorded', 'school_class', 'student', 'recorded_by')
    autocomplete_fields = ['student', 'subject', 'school_class', 'recorded_by'] # Easier selection
    readonly_fields = ('date_recorded', 'last_updated') # Prevent manual editing

# Direct ModelAdmin for TeacherProfile (optional)
# Uncomment if you want to manage TeacherProfile separately
@admin.register(TeacherProfile)
class TeacherProfileAdmin(ImportExportModelAdmin):
     list_display = ('user',)
     search_fields = (
         'user__username',
         'user__first_name',
         'user__last_name',
     )

# Direct ModelAdmin for ParentProfile
@admin.register(ParentProfile)
class ParentProfileAdmin(ImportExportModelAdmin):
    list_display = ('user',)
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
    )

# Register Announcement model
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'timestamp')
    list_filter = ('timestamp', 'posted_by')
    search_fields = ('title', 'content', 'posted_by__username')
    readonly_fields = ('timestamp',) # Timestamp is auto-set

    # Auto-set posted_by to current user when adding in admin
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Only set on creation
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)

# Register AttendanceRecord models
@admin.register(AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'school_class', 'recorded_by')
    list_filter = ('date', 'status', 'school_class', 'student__current_class') # Filter by status, class, etc.
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id', 'date')
    autocomplete_fields = ['student', 'recorded_by', 'school_class']
    list_editable = ('status',) # Allow quick status changes in the list view
    date_hierarchy = 'date' # Add date navigation

    # Limit student choices based on selected class (optional improvement)
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "student":
    #         # This requires more complex logic, potentially using JS or limiting based on user
    #         pass
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(CarouselImage)
class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'uploaded_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'caption')
    list_editable = ('order', 'is_active') # Allow quick edits in list

# --- Inline Admin for News Images ---
class NewsImageInline(admin.StackedInline): # Or admin.TabularInline for more compact view
    model = NewsImage
    extra = 1 # Show 1 blank inline form by default
    fields = ('image', 'caption', 'order') # Fields to show in inline

# --- Admin for News Articles ---
@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_date', 'author', 'created_at')
    list_filter = ('published_date', 'author')
    search_fields = ('title', 'content')
    inlines = [NewsImageInline] # Add the image inline here
    readonly_fields = ('created_at', 'updated_at')

    # Auto-set author on creation
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Only on creation
            obj.author = request.user
        super().save_model(request, obj, form, change)

    # Optional: If using django-import-export, inherit here too
    # class NewsArticleAdmin(ImportExportModelAdmin): ...

# Optionally register NewsImage separately if needed (usually not necessary with inline)
# @admin.register(NewsImage)
# class NewsImageAdmin(admin.ModelAdmin):
#     list_display = ('article', 'caption', 'order')