from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()
from app.models import Products, Order, Cripto, ReferralLink


def edit_text(markup, param):
    if not markup:
        markup = InlineKeyboardMarkup()
    edit = InlineKeyboardButton(text='Изменить текст', callback_data=f'edit_text|{param}')
    markup.add(edit)
    return markup


""" Кнопки главного меню """


def menu():
    markup = InlineKeyboardMarkup()
    catalog = InlineKeyboardButton('Каталог', callback_data='catalog|all|1')
    profile = InlineKeyboardButton('Мой профиль', callback_data='profile')
    manager_chat = InlineKeyboardButton('Чат с менеджером', callback_data='manager_chat')
    reviews = InlineKeyboardButton(text='Чат с отзывами', url='https://t.me/Pay_Unlimited_Chat')
    teh = InlineKeyboardButton(text='Техническая поддержка', url='https://t.me/manager_pu')
    referral_program = InlineKeyboardButton('Реферальная программа', callback_data='referral|1')
    markup.add(catalog)
    markup.add(profile)
    markup.add(referral_program)
    markup.add(manager_chat)
    markup.add(reviews, teh)
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
        products = Products.objects.filter(name__icontains=name, in_bot=True).order_by('name')
    else:
        products = Products.objects.filter(in_bot=True).order_by('name')
    alg_filter = InlineKeyboardButton(text='Поиск по названию',
                                      callback_data=f'catalog|name_filter')
    dont_find = InlineKeyboardButton(text='Не нашел сервис',
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
    manager_chat = InlineKeyboardButton('Чат с менеджером', callback_data='manager_chat')
    back = InlineKeyboardButton('Назад', callback_data=f'catalog|all|{page}')
    markup.add(pay, manager_chat, back)
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
    historys = Order.objects.filter(client=user, status='complite', pay_status='complite',
                                    type__in=['buy', 'not_find_product'])
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
        button = InlineKeyboardButton(text=cripto.name,
                                      callback_data=f'payment|continue|{type}|{order_id}|{cripto.name}')
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


"""Чат с менеджером"""


def go_to_chat(order_id):
    markup = InlineKeyboardMarkup()
    go_to_chat = InlineKeyboardButton('Перейти в чат', callback_data=f'go_to_chat|{order_id}')
    markup.add(go_to_chat)
    return markup


"""Реферальная программа"""


def referral(page, user):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Главное меню', callback_data='menu')
    create = InlineKeyboardButton(text='Создать ссылку', callback_data=f'referral|create|{page}')
    state = InlineKeyboardButton(text='Скачать статистику', callback_data=f'referral|state|{page}')
    markup.add(create, state)
    start = 5 * (int(page) - 1)
    end = 5 * int(page)
    referral_links = ReferralLink.objects.filter(owner=user)
    for referral_link in referral_links[start:end]:
        referral_link_button = InlineKeyboardButton(text=referral_link.name,
                                                    callback_data=f'referral|detail|{referral_link.id}|{page}')
        markup.add(referral_link_button)
    if start > 0:
        last = InlineKeyboardButton(text='<<<',
                                    callback_data=f'referral|{int(page) - 1}')
        markup.add(last)
    if end < len(referral_links):
        next = InlineKeyboardButton(text='>>>',
                                    callback_data=f'referral|{int(page) + 1}')
        markup.add(next)
    markup.add(menu)
    return markup


def referral_go_back(page, link_id):
    markup = InlineKeyboardMarkup(row_width=1)
    menu = InlineKeyboardButton(text='Назад', callback_data=f'referral|{page}')
    delete = InlineKeyboardButton(text='Удалить реферальную ссылку', callback_data=f'referral|delete|{link_id}|{page}')
    markup.add(menu, delete)
    return markup

def referral_back(page):
    markup = InlineKeyboardMarkup()
    menu = InlineKeyboardButton(text='Назад', callback_data=f'referral|{page}')
    markup.add(menu,)
    return markup

def delete_referral(link_id, page):
    markup = InlineKeyboardMarkup()
    yes = InlineKeyboardButton(text='Да', callback_data=f'referral|delete_accept|{link_id}|{page}')
    no = InlineKeyboardButton(text='Нет', callback_data=f'referral|{page}')
    markup.add(yes, no)
    return markup
