import base64
import os
import threading
import time
from io import BytesIO

import django
import openpyxl
from django.db.models import TextField, Count
from django.utils import timezone
from django.utils.translation.trans_real import catalog
from telebot.types import InputFile

import buttons
import payment
import process
from const import bot
from menu import menu
import catalog
import profile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from send_text import send_text

from app.models import ReferralLink, Client, Order, Text, Active_users, BotText



def referral_list(chat_id, user, page):
    send_text('referral_list', chat_id, buttons.referral(user=user, page=page))


def detail_referral(chat_id, link_id, page):
    link = ReferralLink.objects.get(id=link_id)
    users_count =  Client.objects.filter(invite_ref=link).count()
    text = f'Название ссылки: {link.name}\n' \
           f'Денег получено с ссылки: {link.money}\n' \
           f'Приглашенных пользователей: {users_count}\n' \
           f'Ссылка для приглашения: <code>https://t.me/{bot.get_me().username}?start={link.link}</code>'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.referral_go_back(page=page, link_id=link_id), parse_mode='HTML')

def create_referral_link(message, chat_id, user, page):
    if message.content_type == 'text':
        name = message.text
        if len(name) >= 128:
            msg = bot.send_message(chat_id=chat_id, text='Название ссылки не должно превышать 128 символов', reply_markup=buttons.referral_go_back(page))
            bot.register_next_step_handler(msg, create_referral_link, chat_id, user, page)
        else:
            lnk = f'{chat_id}_{name}_{int(time.time())}'
            lnk = str(hash(lnk))[:64]
            link = ReferralLink.objects.create(owner=user, name=name, link=lnk)
            detail_referral(chat_id=chat_id, link_id=link.id, page=page)
    else:
        msg = bot.send_message(chat_id=chat_id, text='Название должно состоять из текста',
                               reply_markup=buttons.referral_go_back(page))
        bot.register_next_step_handler(msg, create_referral_link, chat_id, user, page)


def link_state_data(link):
    name = link.name
    users = Client.objects.filter(invite_ref=link).count()
    new_buy = link.new_user_buy.count()
    try:
        new_conversion = int(new_buy/users*100)
    except Exception:
        new_conversion = 0
    new_products_counts = link.new_user_buy.values('name').annotate(count=Count('name')).order_by('-count')
    new_products_counts_str = ''
    for item in new_products_counts:
        new_products_counts_str += f'{item["name"]} {item["count"]}\n'
    old_buy = link.new_user_buy.count()
    old_products_counts = link.old_user_buy.values('name').annotate(count=Count('name')).order_by('-count')
    old_products_counts_str = ''
    for item in old_products_counts:
        old_products_counts_str += f'{item["name"]} {item["count"]}\n'
    return [name, users, new_buy, new_conversion, new_products_counts_str, old_buy, old_products_counts_str, link.money]


def link_state(wb, user):
    ws = wb.active
    ws.title = "Статистика ссылок"
    data = [['Название ссылки', 'Количество рефералов', 'Количество новых покупок', 'Конверсия', 'Какие сервисы и в каком колчестве оплачивают новые клиенты', 'Количество старых покупок', 'Какие сервисы и в каком колчестве оплачивают старые клиенты', 'Сколько денег заработано']]
    for link in ReferralLink.objects.filter(owner=user):
        data.append(link_state_data(link))
    for row in data:
        ws.append(row)


def state(chat_id, user, page):
    wb = openpyxl.Workbook()
    link_state(wb, user)
    name = f'user_state/Статстика ссылок {chat_id}.xlsx'
    wb.save(name)
    bot.send_document(chat_id=chat_id, document=open(name, 'rb'), reply_markup=buttons.referral_back(page))


def callback(data, user, chat_id):
    if data[0] == 'create':
        msg = send_text('create_ref', chat_id, buttons.referral_back(data[1]))
        bot.register_next_step_handler(msg, create_referral_link, chat_id, user, data[1])
    elif data[0] == 'detail':
        detail_referral(chat_id=chat_id, link_id=data[1], page=data[2])
    elif data[0] == 'state':
        state(chat_id=chat_id, user=user, page=data[1])
    elif data[0] == 'delete':
        bot.send_message(chat_id=chat_id, text='Вы уверены?', reply_markup=buttons.delete_referral(data[1], data[2]))
    elif data[0] == 'delete_accept':
        ReferralLink.objects.get(id=data[1]).delete()
        referral_list(chat_id=chat_id, user=user, page=data[2])
    else:
        referral_list(chat_id=chat_id, user=user, page=data[0])
