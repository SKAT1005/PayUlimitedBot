from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ReferralLink, Client, Manager, Products, Cripto, Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    pass

@admin.register(ReferralLink)
class ReferalLinkAdmin(admin.ModelAdmin):
    fields = ('owner', 'name', 'type', 'last_invite_buyer_user_time')


@admin.register(Client)
class UsrAdmin(admin.ModelAdmin):
    pass

@admin.register(Manager)
class ManagerAdmin(UserAdmin):
    model = Manager
    # Настроим отображение полей в списке пользователей
    list_display = ('username', 'email', 'commission_balance', 'is_friend', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'is_friend')
    search_fields = ('username', 'email')
    ordering = ('username',)

    # Настроим поля для редактирования
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('commission_balance', 'is_friend', 'status')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('commission_balance', 'is_friend', 'status')}),
    )

    # Форма при редактировании
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Убираем пароль с формы редактирования
        if not obj:
            return fieldsets
        return [
            (None, {'fields': ('username', 'password', 'status')}),
            ('Personal info', {'fields': ('commission_balance', 'is_friend')}),
        ]


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'need_enter_price')


@admin.register(Cripto)
class CriptoAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')