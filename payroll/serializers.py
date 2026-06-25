from rest_framework import serializers
from payroll.models import PayrollRun, Paystub, TaxRate


class PaystubSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)

    class Meta:
        model = Paystub
        fields = '__all__'
        read_only_fields = ['total_deductions', 'net_pay', 'created_at']


class PayrollRunSerializer(serializers.ModelSerializer):
    paystubs = PaystubSerializer(many=True, read_only=True)
    processed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = ['total_gross', 'total_taxes', 'total_net', 'created_at']

    def get_processed_by_name(self, obj):
        return str(obj.processed_by) if obj.processed_by else ''


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'
