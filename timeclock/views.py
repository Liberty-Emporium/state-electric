from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from timeclock.models import TimeEntry


class TimeEntryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = TimeEntry.objects.filter(employee=request.user).order_by('-date', '-time_in')[:50]
        data = []
        for e in entries:
            data.append({
                'id': e.id,
                'date': str(e.date),
                'time_in': str(e.time_in) if e.time_in else '',
                'time_out': str(e.time_out) if e.time_out else '',
                'hours_worked': getattr(e, 'hours_worked', 0) or 0,
                'notes': getattr(e, 'notes', '') or '',
            })
        return Response(data)


class ClockInView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        # Check if already clocked in
        active_entry = TimeEntry.objects.filter(employee=user, time_out__isnull=True).first()
        if active_entry:
            return Response({'error': 'Already clocked in', 'time_in': active_entry.time_in}, status=400)

        entry = TimeEntry.objects.create(
            employee=user,
            time_in=timezone.now(),
            notes=request.data.get('notes', ''),
        )
        return Response(TimeEntrySerializer(entry).data)


class ClockOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        entry = TimeEntry.objects.filter(employee=user, time_out__isnull=True).first()
        if not entry:
            return Response({'error': 'Not clocked in'}, status=400)

        entry.time_out = timezone.now()
        entry.notes = request.data.get('notes', entry.notes)
        entry.save()
        return Response(TimeEntrySerializer(entry).data)


class CurrentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        active = TimeEntry.objects.filter(employee=user, time_out__isnull=True).first()
        if active:
            current_hours = round((timezone.now() - active.time_in).total_seconds() / 3600, 2)
            return Response({
                'status': 'clocked_in',
                'time_in': active.time_in,
                'current_hours': current_hours,
            })
        last = TimeEntry.objects.filter(employee=user).first()
        return Response({
            'status': 'clocked_out',
            'last_clock_out': last.time_out if last else None,
        })


class MyTimeHistoryView(generics.ListAPIView):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeEntry.objects.filter(employee=self.request.user).select_related('employee')


class MyPayHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        entries = TimeEntry.objects.filter(employee=user, time_out__isnull=False)
        weeks = {}
        for entry in entries:
            week_key = entry.date.strftime('%Y-W%U')
            if week_key not in weeks:
                weeks[week_key] = {'week': week_key, 'hours': 0, 'earnings': 0, 'date_range': f"{entry.date} to {entry.date + timedelta(days=6)}"}
            weeks[week_key]['hours'] += float(entry.hours_worked)
            weeks[week_key]['earnings'] += float(entry.earnings)

        result = sorted(weeks.values(), key=lambda x: x['week'], reverse=True)
        for r in result:
            r['hours'] = round(r['hours'], 2)
            r['earnings'] = round(r['earnings'], 2)
        return Response(result)


class EmployeeTimeView(generics.ListAPIView):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only office/admin can see other employees' time
        if self.request.user.role == 'employee':
            return TimeEntry.objects.filter(employee=self.request.user)
        user_id = self.kwargs.get('user_id')
        return TimeEntry.objects.filter(employee_id=user_id)


class ActiveEmployeesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_entries = TimeEntry.objects.filter(time_out__isnull=True).select_related('employee')
        return Response([{
            'employee': str(e.employee),
            'username': e.employee.username,
            'time_in': e.time_in,
            'hours_so_far': round((timezone.now() - e.time_in).total_seconds() / 3600, 2),
        } for e in active_entries])
