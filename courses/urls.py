from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course_list'),
    path('create/', views.create_course, name='create_course'),
    path('edit/<int:pk>/', views.edit_course, name='edit_course'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('<slug:slug>/', views.course_detail_with_tests, name='course_detail'),
    path('enroll/<int:pk>/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/test/<int:test_id>/', views.take_test, name='take_test'),
    path('<int:course_id>/test/<int:test_id>/result/<int:result_id>/', views.test_result_detail, name='test_result_detail'),
    path('lesson/complete/<int:lesson_id>/', views.complete_lesson, name='complete_lesson'),
    path('<int:course_id>/certificado/', views.download_certificate, name='download_certificate'),
    path('<int:course_id>/intentos/', views.manage_attempts, name='manage_attempts'),
    path('<int:course_id>/test/create/', views.create_test, name='create_test'),
    path('<int:course_id>/test/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('<int:course_id>/test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
] 