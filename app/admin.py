from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ReferralLink, Client, Manager, Products, Cripto, Order, BalanceHistory, ManagerActions, Active_users, Mailing, Comission, BotText






@admin.register(BotText)
class BotTextAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Comission)
class ComissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    pass

@admin.register(BalanceHistory)
class BalanceHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Active_users)
class Active_usersAdmin(admin.ModelAdmin):
    pass


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'time')
    list_filter = ('client', 'name', 'type', 'time')
    ordering = ('time',)


@admin.register(ManagerActions)
class ManagerActionsAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для модели ManagerActions.
    """
    list_display = ('manager', 'action', 'time')  # Поля, отображаемые в списке
    list_filter = ('manager', 'time')
    search_fields = ('action', 'manager__username')
    ordering = ('-time',)
    date_hierarchy = 'time'
    list_per_page = 25


@admin.register(ReferralLink)
class ReferalLinkAdmin(admin.ModelAdmin):
    fields = ('owner', 'name', 'type', 'last_invite_buyer_user_time')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'username']
    search_fields = ('username', 'id')


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
        ('Personal info', {'fields': ('commission_balance', 'is_friend', 'is_accountant', 'status')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'password1', 'password2')}),
        ('Personal info', {'fields': ('commission_balance', 'is_friend', 'is_accountant', 'status')}),
    )

    # Форма при редактировании
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Убираем пароль с формы редактирования
        if not obj:
            return fieldsets
        return [
            (None, {'fields': ('username', 'password', 'status')}),
            ('Personal info', {'fields': ('commission_balance', 'is_friend', 'is_accountant',)}),
        ]


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'need_enter_price')


@admin.register(Cripto)
class CriptoAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')
