from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from files.models import BusinessDocument
from files.serializers import DocumentSerializer


class FileListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = BusinessDocument.objects.all()
        category = self.request.query_params.get('category')
        folder = self.request.query_params.get('folder')
        customer = self.request.query_params.get('customer')
        if category:
            qs = qs.filter(category=category)
        if folder:
            qs = qs.filter(folder=folder)
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = BusinessDocument.objects.all()


class FileDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        doc = BusinessDocument.objects.get(pk=pk)
        response = HttpResponse(doc.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{doc.title}"'
        return response
