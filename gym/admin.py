from django.contrib import admin
from .models import Customer, Membership, DailyEntry, Product, Sale, SaleItem

admin.site.register(Customer)
admin.site.register(Membership)
admin.site.register(DailyEntry)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleItem)