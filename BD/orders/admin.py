from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "first_name",
        "last_name",
        "email",
        "city",
        "paid",
        "created",
        "updated",
    ]
    list_filter = ["paid", "created", "updated", "city"] 
    search_fields = ["first_name", "last_name", "email", "city", "id"] 
    readonly_fields = ["created", "updated"] 
    inlines = [OrderItemInline] 

    def get_total_cost(self, obj):
        return obj.get_total_cost()
    get_total_cost.short_description = "Total Cost" 

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "product",
        "price",
        "quantity",
        "get_cost",
    ]
    list_filter = ["order", "product"]
    search_fields = ["order__id", "product__name"] 
    readonly_fields = ["price", "quantity"] 

    def get_cost(self, obj):
        return obj.get_cost()
    get_cost.short_description = "Cost"