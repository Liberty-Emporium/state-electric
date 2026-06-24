from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.ReportsSummaryView.as_view()),
    path('revenue/', views.RevenueReportView.as_view()),
    path('outstanding/', views.OutstandingReportView.as_view()),
    path('payroll/', views.PayrollReportView.as_view()),
]
