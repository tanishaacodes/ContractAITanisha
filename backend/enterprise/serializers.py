"""
DRF Serializers for Enterprise Risk Intelligence
"""
from rest_framework import serializers
from .models import Supplier, Commodity, ContractSupplier, ContractCommodity, GeoPoliticalRisk, MonteCarloSimulation
from core.models import Contract


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class CommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = '__all__'


class GeoPoliticalRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoPoliticalRisk
        fields = '__all__'


class MonteCarloSimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonteCarloSimulation
        fields = '__all__'


class ContractSupplierSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = ContractSupplier
        fields = '__all__'


class ContractCommoditySerializer(serializers.ModelSerializer):
    commodity = CommoditySerializer(read_only=True)

    class Meta:
        model = ContractCommodity
        fields = '__all__'
