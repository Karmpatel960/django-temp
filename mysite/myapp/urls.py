from django.urls import path
from . import views

urlpatterns = [
    path('',views.landing,name="landing"),


    path('faculty_login/',views.facultyLogin,name="facultyLogin"),
    path('faculty_register/',views.facultyRegister,name="facultyRegister"),
    # path('faculty_details/',views.facultyDetails,name='facultyDetails'),
    path('faculty_dashboard/',views.facultyDashboard,name='facultyDashboard'),
    path('faculty_profile/',views.facultyProfile,name='facultyProfile'),
    path('faculty_classCreate/',views.facultyClassCreate,name='facultyClassCreate'),
    path('assignment_submissions/<str:pk>',views.assignmentSubmissions,name='assignmentSubmissions'),
    path('class_attendence/<str:pk>',views.classAttendence,name='classAttendence'),
    path('faculty_attendence/<str:pk>',views.classAttendence,name='facultyAttendencePage'),
    path('faculty_assignment/<str:pk>',views.facultySubject,name='facultyAssignment'),
    path('faculty_material/<str:pk>',views.facultySubject,name='facultyMaterial'),
    path('faculty_meeting/<str:pk>',views.facultyMeeting,name='facultyMeeting'),
    path('class_members/<str:pk>',views.classMembersList,name='classMembersList'),
    path('offline_opted_list/<str:pk>',views.offlineOptedList,name='offlineOptedList'),
    path('faculty_subject/<str:pk>',views.facultySubject,name='facultySubject'),
    path('faculty_profileView/<str:pk>',views.facultyProfileView,name='facultyProfileView'),
    path('faculty_logout/',views.facultyLogout,name='facultyLogout'),



    path('student_login/',views.studentLogin,name="studentLogin"),
    path('student_register/',views.studentRegister,name="studentRegister"),
    # path('student_details/',views.studentDetails,name='studentDetails'),
    path('student_dashboard/',views.studentDashboard,name='studentDashboard'),
    path('student_classes/',views.studentClasses,name='studentClasses'),
    path('student_profile/',views.studentProfile,name='studentProfile'),
    path('student_subject/<str:pk>',views.studentSubject,name='studentSubject'),
    path('student_assignment/',views.studentAssignment,name='studentAssignment'),
    path('student_logout/',views.studentLogout,name='studentLogout'),

    # Password Reset URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:uidb64>/<str:token>/', views.reset_password, name='reset_password'),
]
