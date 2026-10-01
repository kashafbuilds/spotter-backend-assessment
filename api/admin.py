from django.contrib import admin

from .models import Product, FuelStation


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'created_at')


@admin.register(FuelStation)
class FuelStationAdmin(admin.ModelAdmin):
    list_display = ('id', 'truckstop_name', 'city', 'state', 'retail_price')