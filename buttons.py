from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()
from app.models import Products, Order, Cripto

""" Кнопки главного меню """


def menu():
    markup = InlineKeyboardMarkup(row_width=1)
    catalog = InlineKeyboardButton('Каталог', callback_data='catalog|all|1')
    profile = InlineKeyboardButton('Мой профиль', callback_data='profile')
    manager_chat = InlineKeyboardButton('Чат с менеджеров', callback_data='manager_chat')
    referral_program = InlineKeyboardButton('Реферальная программа', callback_data='referral_program|1')
    markup.add(catalog, profile, manager_chat, referral_program)
    return markup


def go_to_menu():
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(menu)
    return markup


""" Кнопки каталога """


def catalog_list(page, param='all', name=None):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    start = 5 * (int(page) - 1)
    end = 5 * int(page)
    if param == 'name':
        products = Products.objects.filter(name__icontains=name)
    else:
        products = Products.objects.all()
    alg_filter = InlineKeyboardButton(text='Поиск по названию',
                                      callback_data=f'catalog|name_filter')
    dont_find = InlineKeyboardButton(text='Не нашел свой сервис',
                                     callback_data=f'catalog|dont_find')
    markup.add(alg_filter, dont_find)
    for product in products[start:end]:
        product_button = InlineKeyboardButton(text=product.name,
                                              callback_data=f'catalog|detail|{product.id}|{page}')
        markup.add(product_button)
    if start > 0:
        if name:
            last = InlineKeyboardButton(text='<<<',
                                        callback_data=f'catalog|{param}|{name}{int(page) - 1}')
        else:
            last = InlineKeyboardButton(text='<<<',
                                        callback_data=f'catalog|{param}|{int(page) - 1}')
        markup.add(last)
    if end < len(products):
        if name:
            next = InlineKeyboardButton(text='>>>',
                                        callback_data=f'catalog|{param}|{name}|{int(page) + 1}')
        else:
            next = InlineKeyboardButton(text='>>>',
                                        callback_data=f'catalog|{param}|{int(page) + 1}')
        markup.add(next)
    markup.add(menu)
    return markup


def prod_detail(page, prod_id):
    markup = InlineKeyboardMarkup(row_width=1)
    pay = InlineKeyboardButton('Перейти к оплате', callback_data=f'payment|buy|{prod_id}')
    back = InlineKeyboardButton('Назад', callback_data=f'catalog|all|{page}')
    markup.add(pay, back)
    return markup


"""Кнопки меню"""


def profile():
    markup = InlineKeyboardMarkup(row_width=1)
    pay = InlineKeyboardButton('Пополнить баланс', callback_data=f'payment|top_up')
    history = InlineKeyboardButton('История заказов', callback_data=f'profile|history|1')
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(pay, history, menu)
    return markup


def history(page, user):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    start = 5 * (int(page) - 1)
    end = 5 * int(page)
    historys = Order.objects.filter(client=user, status='complite', type='buy')
    for history in historys[start:end]:
        product_button = InlineKeyboardButton(text=history.name,
                                              callback_data=f'profile|history_detail|{history.id}|{page}')
        markup.add(product_button)
    if start > 0:
        last = InlineKeyboardButton(text='<<<',
                                    callback_data=f'profile|history|{int(page) - 1}')
        markup.add(last)
    if end < len(historys):
        next = InlineKeyboardButton(text='>>>',
                                    callback_data=f'profile|history|{int(page) + 1}')
        markup.add(next)
    markup.add(menu)
    return markup


def history_detail(page):
    markup = InlineKeyboardMarkup(row_width=1)
    back = InlineKeyboardButton(text='Назад', callback_data=f'profile|history|{page}')
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    markup.add(back, menu)
    return markup


"""Кнопки оплаты"""


def payment_method(order_id, need_enter_new_amount=False, top_up=False):
    markup = InlineKeyboardMarkup(row_width=1)
    if not top_up:
        balance = InlineKeyboardButton('Баланс профиля', callback_data=f'payment|continue|balance|{order_id}')
        markup.add(balance)
    bybit = InlineKeyboardButton('Bybit', callback_data=f'payment|continue|bybit|{order_id}')
    wallet = InlineKeyboardButton('Telegram Wallet', callback_data=f'payment|continue|wallet|{order_id}')
    card = InlineKeyboardButton('Банковская карта', callback_data=f'payment|continue|card|{order_id}')
    markup.add(bybit, wallet, card)
    if need_enter_new_amount:
        enter_new_summ = InlineKeyboardButton('Ввести новую сумму',
                                              callback_data=f'payment|enter_new_amount|{order_id}')
        markup.add(enter_new_summ)
    back = InlineKeyboardButton(text='Назад', callback_data=f'payment|menu|{order_id}')
    markup.add(back)
    return markup

def coose_cripto(type, order_id):
    markup = InlineKeyboardMarkup(row_width=1)
    for cripto in Cripto.objects.all():
        button = InlineKeyboardButton(text=cripto.name, callback_data=f'payment|continue|{type}|{order_id}|{cripto.name}')
        markup.add(button)
    return markup


def accept(order_id, type):
    markup = InlineKeyboardMarkup(row_width=1)
    accept = InlineKeyboardButton(text='✅ Подтвердить ✅', callback_data=f'payment|accept|{order_id}|{type}')
    cansel = InlineKeyboardButton(text='❌ Отменить и вернуться в главное меню ❌', callback_data='menu')
    change_payment_method = InlineKeyboardButton(text='Изменить способ оплаты',
                                                 callback_data=f'payment|change_payment_method|{order_id}')
    markup.add(accept, change_payment_method, cansel)
    return markup