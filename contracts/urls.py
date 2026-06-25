from django.urls import path
from . import views

urlpatterns = [
    path('', views.ContractViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', views.ContractViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('<int:pk>/line-items/', views.ContractLineItemView.as_view()),
    path('dashboard/', views.ContractDashboardView.as_view()),
]
