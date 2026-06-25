from django.urls import path
from . import views

urlpatterns = [
    path('runs/', views.PayrollRunViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('runs/<int:pk>/', views.PayrollRunViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'})),
    path('paystubs/', views.PaystubViewSet.as_view({'get': 'list'})),
    path('paystubs/<int:pk>/', views.PaystubViewSet.as_view({'get': 'retrieve'})),
    path('my-paystubs/', views.MyPaystubsView.as_view()),
    path('tax-rates/', views.TaxRateViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tax-rates/<int:pk>/', views.TaxRateViewSet.as_view({'get': 'retrieve', 'put': 'update'})),
]
