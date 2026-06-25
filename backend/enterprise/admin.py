from django.contrib import admin
from .models import (
    Supplier,
    Commodity,
    ContractSupplier,
    ContractCommodity,
    GeoPoliticalRisk,
    MonteCarloSimulation
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'country', 'risk_level', 'risk_score', 'exposure_amount']
    list_filter = ['tier', 'risk_level', 'country', 'is_single_source']
    search_fields = ['name', 'country']
    ordering = ['name']


@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_price', 'currency', 'volatility', 'drift', 'total_exposure']
    list_filter = ['category', 'currency']
    search_fields = ['name', 'category']
    ordering = ['name']


@admin.register(GeoPoliticalRisk)
class GeoPoliticalRiskAdmin(admin.ModelAdmin):
    list_display = ['country', 'region', 'risk_severity', 'political_stability_score', 'has_active_sanctions', 'total_exposure']
    list_filter = ['region', 'risk_severity', 'has_active_sanctions']
    search_fields = ['country', 'region']
    ordering = ['country']


@admin.register(MonteCarloSimulation)
class MonteCarloSimulationAdmin(admin.ModelAdmin):
    list_display = ['contract', 'iterations', 'mean_exposure', 'var_95', 'var_99', 'created_at']
    list_filter = ['iterations', 'created_at']
    search_fields = ['contract__original_filename']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(ContractSupplier)
class ContractSupplierAdmin(admin.ModelAdmin):
    list_display = ['contract', 'supplier', 'exposure_amount', 'dependency_level']
    list_filter = ['dependency_level']
    search_fields = ['contract__original_filename', 'supplier__name']


@admin.register(ContractCommodity)
class ContractCommodityAdmin(admin.ModelAdmin):
    list_display = ['contract', 'commodity', 'quantity', 'unit_price', 'total_value']
    search_fields = ['contract__original_filename', 'commodity__name']
