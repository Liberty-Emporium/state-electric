from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from timeclock.models import TimeEntry


def entry_to_dict(e):
    return {
        'id': e.id,
        'date': str(e.date),
        'time_in': str(e.time_in) if e.time_in else '',
        'time_out': str(e.time_out) if e.time_out else '',
        'hours_worked': getattr(e, 'hours_worked', 0) or 0,
        'earnings': getattr(e, 'earnings', 0) or 0,
        'notes': getattr(e, 'notes', '') or '',
        'employee': e.employee.get_full_name() or e.employee.username,
        'username': e.employee.username,
    }


class TimeEntryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = TimeEntry.objects.filter(employee=request.user).order_by('-date', '-time_in')[:50]
        return Response([entry_to_dict(e) for e in entries])


class ClockInView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        active_entry = TimeEntry.objects.filter(employee=user, time_out__isnull=True).first()
        if active_entry:
            return Response({'error': 'Already clocked in', 'time_in': active_entry.time_in}, status=400)
        entry = TimeEntry.objects.create(
            employee=user,
            time_in=timezone.now(),
            notes=request.data.get('notes', ''),
        )
        return Response(entry_to_dict(entry))


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
        return Response(entry_to_dict(entry))


class CurrentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        active = TimeEntry.objects.filter(employee=user, time_out__isnull=True).first()
        if active:
            current_hours = round((timezone.now() - active.time_in).total_seconds() / 3600, 2)
            return Response({'status': 'clocked_in', 'time_in': str(active.time_in), 'current_hours': current_hours})
        last = TimeEntry.objects.filter(employee=user).first()
        return Response({'status': 'clocked_out', 'last_clock_out': str(last.time_out) if last else None})


class MyTimeHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        entries = TimeEntry.objects.filter(employee=request.user).order_by('-date', '-time_in')[:50]
        return Response([entry_to_dict(e) for e in entries])


class MyPayHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        entries = TimeEntry.objects.filter(employee=user, time_out__isnull=False)
        weeks = {}
        for entry in entries:
            week_key = entry.date.strftime('%Y-W%U')
            if week_key not in weeks:
                weeks[week_key] = {'week': week_key, 'hours': 0, 'earnings': 0}
            weeks[week_key]['hours'] += float(getattr(entry, 'hours_worked', 0) or 0)
            weeks[week_key]['earnings'] += float(getattr(entry, 'earnings', 0) or 0)
        result = sorted(weeks.values(), key=lambda x: x['week'], reverse=True)
        for r in result:
            r['hours'] = round(r['hours'], 2)
            r['earnings'] = round(r['earnings'], 2)
        return Response(result)


class EmployeeTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == 'employee':
            entries = TimeEntry.objects.filter(employee=request.user)
        else:
            user_id = request.kwargs.get('user_id')
            entries = TimeEntry.objects.filter(employee_id=user_id)
        return Response([entry_to_dict(e) for e in entries.order_by('-date')[:50]])


class ActiveEmployeesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_entries = TimeEntry.objects.filter(time_out__isnull=True)
        return Response([{
            'employee': e.employee.get_full_name() or e.employee.username,
            'username': e.employee.username,
            'time_in': str(e.time_in),
            'hours_so_far': round((timezone.now() - e.time_in).total_seconds() / 3600, 2),
        } for e in active_entries])
