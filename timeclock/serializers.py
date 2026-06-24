from rest_framework import serializers
from timeclock.models import TimeEntry


class TimeEntrySerializer(serializers.ModelSerializer):
    hours_worked = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    earnings = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntry
        fields = '__all__'
        read_only_fields = ['created_at', 'hours_worked', 'earnings']

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() or obj.employee.username
