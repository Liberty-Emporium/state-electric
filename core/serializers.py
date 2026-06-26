from rest_framework import serializers
from core.models import Customer, Vendor


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    full_name = serializers.SerializerMethodField()
    role = serializers.CharField()
    role_display = serializers.SerializerMethodField()
    phone = serializers.CharField()
    is_active = serializers.BooleanField()
    is_active_employee = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_role_display(self, obj):
        return obj.get_role_display()

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_role_display(self, obj):
        return obj.get_role_display()


class CustomerSerializer(serializers.ModelSerializer):
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    invoice_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'

    def get_invoice_count(self, obj):
        return obj.invoices.count()


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
