from django.urls import path
from django.views.generic import TemplateView
from . import views
from . import dashboard_views

urlpatterns = [
    path('summary/', views.ReportsSummaryView.as_view()),
    path('revenue/', views.RevenueReportView.as_view()),
    path('outstanding/', views.OutstandingReportView.as_view()),
    path('payroll/', views.PayrollReportView.as_view()),
    # Dashboard page (HTML)
    path('overview/', TemplateView.as_view(template_name='reports/dashboard.html')),
    # Dashboard API endpoints
    path('dashboard/', dashboard_views.DashboardSummaryView.as_view()),
    path('dashboard/financials/', dashboard_views.FinancialGraphsView.as_view()),
    path('dashboard/revenue-trend/', dashboard_views.RevenueTrendView.as_view()),
    path('dashboard/top-customers/', dashboard_views.TopCustomersView.as_view()),
    path('dashboard/recent-activity/', dashboard_views.RecentActivityView.as_view()),
    path('dashboard/ask/', dashboard_views.AIQueryView.as_view()),
]
