from django.urls import path
from . import views

urlpatterns = [
    path('', views.FileListCreateView.as_view()),
    path('<int:pk>/', views.FileDetailView.as_view()),
    path('<int:pk>/download/', views.FileDownloadView.as_view()),
]
