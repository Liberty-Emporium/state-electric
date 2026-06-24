from django.urls import path
from .payment_views import PaymentListView, PaymentDetailView, PaymentByMethodView

urlpatterns = [
    path('', PaymentListView.as_view()),
    path('<int:pk>/', PaymentDetailView.as_view()),
    path('by-method/', PaymentByMethodView.as_view()),
]
