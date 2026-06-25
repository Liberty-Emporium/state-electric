from rest_framework import serializers
from contracts.models import Contract, ContractLineItem


class ContractLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractLineItem
        fields = '__all__'
        read_only_fields = ['amount']


class ContractSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    line_items = ContractLineItemSerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'amount']

    def get_created_by_name(self, obj):
        return str(obj.created_by) if obj.created_by else ''


class ContractSummarySerializer(serializers.Serializer):
    total_contracts = serializers.IntegerField()
    active_contracts = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    by_status = serializers.DictField(required=False)
