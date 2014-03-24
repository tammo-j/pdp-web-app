from django.contrib import admin
from orders.models import Category, Product, Order, OrderItem, Setting

class ItemInline(admin.TabularInline):
    model = OrderItem

class OrderAdmin(admin.ModelAdmin):
    inlines = [ ItemInline, ]

admin.site.register(Setting)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order, OrderAdmin)
