import decimal
import os
import time

import django
import requests
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from app.models import Cripto, BalanceHistory, Client

def get_balance():
    while True:
        total_balance = Client.objects.aggregate(total=Sum('balance'))['total']
        if total_balance:
            BalanceHistory.objects.create(total_balance=total_balance)
        else:
            BalanceHistory.objects.create(total_balance=0)
        time.sleep(60 * 60 * 24)