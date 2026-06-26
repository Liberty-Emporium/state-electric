from django.urls import path
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection


class CustomerListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, phone, email, is_active FROM core_customer ORDER BY name")
            rows = cursor.fetchall()
        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'name': row[1] or '',
                'phone': row[2] or '',
                'email': row[3] or '',
                'is_active': row[4] if row[4] is not None else True,
                'contact_name': '',
                'company': '',
                'billing_address': '',
                'shipping_address': '',
                'notes': '',
                'outstanding_balance': '0',
            })
        return Response(data)


class CustomerDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, phone, email, is_active FROM core_customer WHERE id = %s", [pk])
            row = cursor.fetchone()
        if not row:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': row[0],
            'name': row[1] or '',
            'phone': row[2] or '',
            'email': row[3] or '',
            'is_active': row[4] if row[4] is not None else True,
        })


urlpatterns = [
    path('', CustomerListView.as_view()),
    path('<int:pk>/', CustomerDetailView.as_view()),
]
