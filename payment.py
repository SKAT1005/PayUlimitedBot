import decimal
import os

import django

import buttons

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()
from app.models import Order, Cripto, Products, Manager
from const import bot
from menu import menu
from send_text import send_text

data = {
    'bybit': 'UID `19813935`',
    'wallet': '`https://t.me/manager_pu`'
}


def continue_payment(chat_id, user, order_id, type, currency=None):
    order = Order.objects.get(id=order_id)
    order.payment_type = type
    order.save(update_fields=['payment_type'])
    attention = ''
    if type == 'card':
        usdt_cource = Cripto.objects.get(name='USDT').course
        price_in_rub = round(order.total_product_price * usdt_cource)
        order.total_product_price_str = f'{price_in_rub}₽'
    else:
        order.total_product_price_str = f'{order.total_product_price}$'
    order.save(update_fields=['total_product_price_str'])
    if Manager.objects.filter(status='online').count() == 0:
        attention = '\n\nВнимание! На данный момент все менеджеры заняты, время ответа может быть больше обычного. С вами свяжется первый освободившийся менеджер.'
    if type == 'balance':
        if user.balance < order.total_product_price:
            text = 'На вашем балансе недостаточно средств. Выберите другой способ оплаты'
            bot.send_message(chat_id=chat_id,
                             text=text,
                             reply_markup=buttons.payment_method(order_id=order_id, top_up=True))
        else:
            text = f'При подтверждении с вашего баланса спишется {order.total_product_price_str}'
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.accept(order_id=order_id, type=type))
    elif type == 'card':
        text = f'У вас к оплате {order.total_product_price_str} рублей. Подтвердите то, что вы хотите произвести оплату переводом рублей.\n\n ' \
               'После подтверждения с вами свяжется менеджер, чтобы передать вам реквизиты для оплаты\n\n' \
               'Гайд на перевод денег 👉 https://t.me/+ZDgdxKDKd35iZDV\n\n' \
               'FAQ\n\n' \
               '- Почему курс выше чем у ЦБ?\n\n' \
               '<blockquote>Мы не принимаем деньги на личные реквизиты. Реквизиты нам выдает эквайринг. Для оплаты нам надо пополнить зарубежную карту в долларах. Сделать это можно, только через эквайринг. Эквайринг хочет заработать и завышает курс.</blockquote>'
        bot.send_message(chat_id=chat_id,
                         text=text + attention,
                         reply_markup=buttons.accept(order_id=order_id, type=type), parse_mode='HTML')
    else:
        if not currency:
            text = 'Выберите валюту, которой хотите произвести оплату'
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.coose_cripto(type=type, order_id=order_id))
        else:
            text = f'Отправьте {order.total_product_price_str} на {data[type]} и нажмите кнопку подтвердить' + attention
            text = text.replace('.', '\.').replace('!', '\!')
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.accept(order_id=order_id, type=type), parse_mode='MarkDownV2')


def calculate_total_price(amount):
    total_amount = amount
    if amount <= 20:
        total_amount *= decimal.Decimal(1.25)
    elif amount <= 50:
        total_amount *= decimal.Decimal(1.15)
    else:
        total_amount *= decimal.Decimal(1.1)
    return round(total_amount, 2)


def create_order(user, amount, total_amount, product=False):
    if product:
        if user.orders_for_user.filter(type='buy').count() == 0:
            is_first_buy = True
        else:
            is_first_buy = False
        order = Order.objects.create(
            client=user,
            name=product.name,
            product_price=amount,
            total_product_price=total_amount,
            is_first_buy=is_first_buy,
            type='buy'
        )
    else:
        order = Order.objects.create(
            client=user,
            product_price=amount,
            total_product_price=total_amount,
            type='top_up'
        )
    return order


def tup_up_balance(message, chat_id, user, order_id=False, product=False):
    if message.content_type == 'text':
        try:
            amount = decimal.Decimal(message.text.replace(',', '.'))
            total_product_price = amount
        except Exception:
            msg = send_text('top_up', chat_id, buttons.go_to_menu())
            bot.register_next_step_handler(msg, tup_up_balance, chat_id, user)
        else:
            if product:
                total_product_price = calculate_total_price(amount)
                top_up = False
            else:
                top_up = True
            if order_id:
                order = Order.objects.get(id=order_id)
                if order.type != 'top_up':
                    total_product_price = calculate_total_price(amount)
                order.product_price = amount
                order.total_product_price = total_product_price
                order.save(update_fields=['product_price', 'total_product_price'])
            else:
                order = create_order(user=user, amount=amount, total_amount=total_product_price, product=product)
            text = f'У вас к оплате {total_product_price}$. Выберите способ оплаты'
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.payment_method(order_id=order.id, need_enter_new_amount=True,
                                                                 top_up=top_up))


def buy_step_one(chat_id, user, prod_id):
    product = Products.objects.get(id=prod_id)
    if product.need_enter_price:
        msg = send_text('enter_price', chat_id, buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user, False, product)
    else:
        amount = product.price
        order = create_order(user=user, amount=amount, total_amount=amount, product=product)
        text = f'У вас к оплате {amount}$. Выберите способ оплаты'
        bot.send_message(chat_id=chat_id, text=text,
                         reply_markup=buttons.payment_method(order_id=order.id, need_enter_new_amount=False))


def change_payment_method(chat_id, order_id):
    order = Order.objects.get(id=order_id)
    text = f'У вас к оплате {order.total_product_price}$. Выберите новый способ оплаты'
    if order.type == 'tup_up':
        bot.send_message(chat_id=chat_id, text=text,
                         reply_markup=buttons.payment_method(order_id=order.id,
                                                             top_up=True))
    else:
        bot.send_message(chat_id=chat_id, text=text,
                         reply_markup=buttons.payment_method(order_id=order.id, top_up=False))


def accept(chat_id, user, order_id, type):
    order = Order.objects.get(id=order_id)
    order.status = 'wait_manager'
    order.save(update_fields=['status'])
    if type == 'balance':
        user.balance -= order.total_product_price
        user.save(update_fields=['balance'])
        order.pay_status = 'complite'
        order.save(update_fields=['pay_status'])
    user.order_id = order_id
    user.save(update_fields=['order_id'])
    if order.payment_type == 'bybit':
        send_text('bybit', chat_id, buttons.go_to_menu())
    elif order.payment_type == 'wallet':
        send_text('wallet', chat_id, buttons.go_to_menu())
    elif order.payment_type == 'card':
        send_text('card', chat_id, buttons.go_to_menu())
    elif order.payment_type == 'balance':
        send_text('balance', chat_id, buttons.go_to_menu())


def callback(data, user, chat_id):
    if data[0] == 'buy':
        buy_step_one(chat_id=chat_id, prod_id=data[1], user=user)
    elif data[0] == 'top_up':
        msg = send_text('top_up', chat_id, buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user)
    elif data[0] == 'enter_new_amount':
        msg = send_text('enter_price', chat_id, buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user, data[1])
    elif data[0] == 'continue':
        if len(data) == 3:
            continue_payment(chat_id=chat_id, user=user, type=data[1], order_id=data[2])
        else:
            continue_payment(chat_id=chat_id, user=user, type=data[1], order_id=data[2], currency=data[3])
    elif data[0] == 'change_payment_method':
        change_payment_method(chat_id=chat_id, order_id=data[1])
    elif data[0] == 'accept':
        accept(chat_id=chat_id, user=user, order_id=data[1], type=data[2])
    elif data[0] == 'menu':
        try:
            Order.objects.get(id=data[1]).delete()
        except Exception:
            pass
        menu(chat_id=chat_id)
