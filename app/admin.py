from django.contrib import admin
from .models import ReferralLink, Client, Manager, Products, Cripto


@admin.register(ReferralLink)
class ReferalLinkAdmin(admin.ModelAdmin):
    fields = ('owner', 'name', 'type', 'last_invite_buyer_user_time')


@admin.register(Client)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    fields = ('username', 'password', 'commission_balance', 'groups')


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'need_enter_price')


@admin.register(Cripto)
class CriptoAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')