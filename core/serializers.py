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


class CustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    company = serializers.CharField()
    contact_name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField()
    billing_address = serializers.CharField()
    shipping_address = serializers.CharField()
    notes = serializers.CharField()
    is_active = serializers.BooleanField()
    outstanding_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    invoice_count = serializers.SerializerMethodField()

    def get_invoice_count(self, obj):
        return 0


class VendorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    contact_name = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()
    notes = serializers.CharField()
    is_active = serializers.BooleanField()
