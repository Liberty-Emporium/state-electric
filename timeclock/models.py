from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeEntry(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='time_entries')
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField()
    time_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date', '-time_in']
        verbose_name = 'Time Entry'
        verbose_name_plural = 'Time Entries'

    def __str__(self):
        time_out_str = self.time_out.strftime('%H:%M') if self.time_out else 'Still Clocked In'
        return f"{self.employee.get_full_name()} - {self.date} ({self.time_in.strftime('%H:%M')} - {time_out_str})"

    @property
    def hours_worked(self):
        if not self.time_out:
            return 0
        delta = self.time_out - self.time_in
        return round(delta.total_seconds() / 3600, 2)

    @property
    def earnings(self):
        return round(self.hours_worked * float(self.employee.hourly_rate), 2)


class TimeSummary(models.Model):
    """Aggregated daily time summary for reporting."""
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_summaries')
    date = models.DateField()
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date}: {self.total_hours}h (${self.total_earnings})"
