from rest_framework import serializers
from core.models import Customer, Vendor


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        from core.models import User
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'role', 'role_display', 'phone', 'is_active',
                  'is_active_employee', 'created_at']
        read_only_fields = ['id', 'created_at']

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
