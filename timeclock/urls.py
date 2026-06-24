from django.urls import path
from . import views

urlpatterns = [
    path('clock-in/', views.ClockInView.as_view()),
    path('clock-out/', views.ClockOutView.as_view()),
    path('current/', views.CurrentStatusView.as_view()),
    path('my-history/', views.MyTimeHistoryView.as_view()),
    path('my-pay/', views.MyPayHistoryView.as_view()),
    path('employee/<int:user_id>/', views.EmployeeTimeView.as_view()),
    path('active-employees/', views.ActiveEmployeesView.as_view()),
]
