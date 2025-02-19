import decimal
import os
import time

import django
import requests
from django.db.models import Sum

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from app.models import Cripto, BalanceHistory, Client


def usdt_cource():
    while True:
        usdt, _ = Cripto.objects.get_or_create(name='USDT')
        url = 'https://min-api.cryptocompare.com/data/price?fsym=USDT&tsyms=RUB'
        response = requests.get(url).json()
        usdt.course = decimal.Decimal(response['RUB']) + 10
        usdt.save()
        time.sleep(60*60*24)

def get_balance():
    while True:
        total_balance = Client.objects.aggregate(total=Sum('balance'))['total']
        if total_balance:
            BalanceHistory.objects.create(total_balance=total_balance)
        else:
            BalanceHistory.objects.create(total_balance=0)
        time.sleep(60 * 60 * 24)