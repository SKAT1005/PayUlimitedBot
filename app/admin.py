from django.contrib import admin
from .models import ReferralLink, Client, Manager


@admin.register(ReferralLink)
class ReferalLinkAdmin(admin.ModelAdmin):
    fields = ('owner', 'name', 'type', 'last_invite_buyer_user_time')


@admin.register(Client)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    fields = ('username', 'password', 'commission_balance', 'groups')
