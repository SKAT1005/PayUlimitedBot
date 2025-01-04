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
        url = 'https://api.binance.com/api/v3/avgPrice?symbol=USDTRUB'
        usdt, _ = Cripto.objects.get_or_create(name='USDT')
        response = requests.get(url)
        usdt.course = decimal.Decimal(response.json()['price']) + 10
        usdt.save()
        time.sleep(60*60*24)

def get_balance():
    while True:
        total_balance = Client.objects.aggregate(total=Sum('balance'))['total']
        BalanceHistory.objects.create(total_balance=total_balance)
        time.sleep(60 * 60 * 24)