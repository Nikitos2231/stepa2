from django.contrib import admin

# Register your models here.
from django.contrib import admin
from shop.models import Customer, Goods

admin.site.register(Customer)
admin.site.register(Goods)
