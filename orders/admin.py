from django.contrib import admin
from orders.models import Category, Product, Order, OrderItem, Setting

class ItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    inlines = [ ItemInline, ]

class ProductAdmin(admin.ModelAdmin):
    search_fields = ['code', 'name', 'category__name']

admin.site.register(Setting)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
