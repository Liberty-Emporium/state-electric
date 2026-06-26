from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from .models import User


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'super_admin'


class IsOffice(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('super_admin', 'office')


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.role in ('super_admin', 'office'):
            return True
        return obj == request.user


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        try:
            user = authenticate(username=username, password=password)
            if user is None:
                return Response({'detail': 'Invalid credentials'}, status=401)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': getattr(user, 'email', '') or '',
                    'first_name': getattr(user, 'first_name', '') or '',
                    'last_name': getattr(user, 'last_name', '') or '',
                    'role': getattr(user, 'role', 'employee'),
                    'phone': getattr(user, 'phone', '') or '',
                    'is_active': getattr(user, 'is_active', True),
                },
            })
        except Exception as e:
            import traceback
            return Response({'detail': str(e), 'trace': traceback.format_exc()[-500:]}, status=500)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': getattr(user, 'email', '') or '',
            'first_name': getattr(user, 'first_name', '') or '',
            'last_name': getattr(user, 'last_name', '') or '',
            'role': getattr(user, 'role', 'employee'),
            'phone': getattr(user, 'phone', '') or '',
            'is_active': getattr(user, 'is_active', True),
        })

    def patch(self, request):
        user = request.user
        for field in ['first_name', 'last_name', 'email', 'phone']:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()
        return Response({'status': 'updated'})


class UserListCreateView(generics.ListCreateAPIView):
    serializer_class = None

    def get_serializer_class(self):
        from .serializers import UserSerializer
        return UserSerializer

    def get_permissions(self):
        return [IsOffice()]

    def get_queryset(self):
        qs = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = None

    def get_serializer_class(self):
        from .serializers import UserSerializer
        return UserSerializer

    permission_classes = [IsOffice]
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class SetPasswordView(APIView):
    permission_classes = [IsOffice]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        password = request.data.get('password', '')
        if len(password) < 4:
            return Response({'error': 'Password too short (min 4)'}, status=400)
        user.set_password(password)
        user.save()
        return Response({'status': 'password updated'})
