from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
    path('outstanding/', views.OutstandingInvoicesView.as_view()),
    path('<int:pk>/add-payment/', views.AddPaymentView.as_view()),
    path('<int:pk>/line-items/', views.InvoiceLineItemView.as_view()),
    path('dashboard/', views.InvoiceDashboardView.as_view()),
]
