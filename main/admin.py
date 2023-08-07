from django.contrib import admin
from .models import *

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'seller')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'item_count', 'total_price')


admin.site.register(Item, ItemAdmin)
admin.site.register(Order, OrderAdmin)
