# core/urls.py
from django.urls import path
from . import views  # Import views from the current directory ('core')

# Define the URL patterns for the 'core' app
urlpatterns = [
    # Map the root URL within this app ('') to the 'home' view
    path('', views.home, name='home'),

    # Map the 'parent/dashboard/' URL to the 'parent_dashboard' view
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),

    # You can add more URLs specific to the 'core' app here later
    # e.g., path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    # Add the teacher dashboard URL
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),

    # URL for adding a result for a specific student
    path('student/<int:student_id>/result/add/', views.add_edit_result, name='add_result'),

    # URL for editing a specific existing result
    path('result/<int:result_id>/edit/', views.add_edit_result, name='edit_result'),

    # Add URL for deleting a specific result
    path('result/<int:result_id>/delete/', views.delete_result, name='delete_result'),

    # Add URL for viewing a specific student's profile
    path('student/<int:student_id>/profile/', views.student_profile, name='student_profile'),

    # Add URL for taking attendance for a specific class
    path('class/<int:class_id>/attendance/', views.take_attendance, name='take_attendance'),

    # Add URL for viewing class attendance history
    path('class/<int:class_id>/attendance/view/', views.view_class_attendance, name='view_class_attendance'),

    # Add URL for exporting class results
    path('class/<int:class_id>/results/export/', views.export_class_results_csv, name='export_class_results'),

    # Add URL for exporting parent's children results
    path('parent/results/export/', views.export_parent_results_csv, name='export_parent_results'),

    # Add URL for the news list page
    path('news/', views.news_list, name='news_list'),
    # Optional: URL for single news detail page
    # path('news/<int:article_id>/', views.news_detail, name='news_detail'),

    path('news/<int:article_id>/', views.news_detail, name='news_detail'),

    # Add URL for the central dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
]