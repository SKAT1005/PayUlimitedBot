import decimal
import os

import django

import buttons

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()
from app.models import Order, Cripto, Products, Manager
from const import bot
from menu import menu

data = {
    'bybit': 'UID `19813935`',
    'wallet': '`https://t.me/manager_pu`'
}


def continue_payment(chat_id, user, order_id, type, currency=None):
    order = Order.objects.get(id=order_id)
    order.payment_type = type
    order.save(update_fields=['payment_type'])
    attention = ''
    if currency:
        cripto = Cripto.objects.get(name=currency)
        price_in_cripto = round(order.total_product_price / cripto.course, cripto.dec)
        order.total_product_price_str = f'{price_in_cripto} {currency}'
    if type in ['balance', 'card']:
        usdt_cource = Cripto.objects.get(name='USDT').course
        order.total_product_price_str = f'{order.total_product_price*usdt_cource} ₽'
    order.save(update_fields=['total_product_price_str'])
    if Manager.objects.filter(status='online').count() == 0:
        attention = '\n\nВнимание! На данный момент все менеджеры заняты, время ответа может быть больше обычного. С вами свяжется первый освободившийся менеджер.'
    if type == 'balance':
        if user.balance <= order.total_product_price:
            text = 'На вашем балансе недостаточно средств. Выберите другой способ оплаты'
            bot.send_message(chat_id=chat_id,
                             text=text,
                             reply_markup=buttons.payment_method(order_id=order_id, top_up=True))
        else:
            text = f'При подтверждении с вашего баланса спишется {order.total_product_price_str}'
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.accept(order_id=order_id, type=type))
    elif type == 'card':
        bot.send_message(chat_id=chat_id,
                         text=f'У вас к оплате {order.total_product_price_str} рублей. Подтвердите то, что вы хотите произвести оплату картой. После подтверждения с вами свяжется менеджер, чтобы передать вам реквезиты для оплаты' + attention,
                         reply_markup=buttons.accept(order_id=order_id, type=type))
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
        except Exception:
            msg = bot.send_message(chat_id=chat_id, text='Введите сумму, на которую хотите пополнить в рублях',
                                   reply_markup=buttons.go_to_menu())
            bot.register_next_step_handler(msg, tup_up_balance, chat_id, user)
        else:
            total_amount = calculate_total_price(amount)
            if order_id:
                order = Order.objects.get(id=order_id)
                order.product_price = amount
                order.total_product_price = total_amount
                order.save(update_fields=['product_price', 'total_product_price'])
            else:
                order = create_order(user=user, amount=amount, total_amount=total_amount, product=product)
            if product:
                top_up = False
            else:
                top_up = True
            text = f'У вас к оплате {total_amount}$. Выберите способ оплаты'
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=buttons.payment_method(order_id=order.id, need_enter_new_amount=True,
                                                                 top_up=top_up))


def buy_step_one(chat_id, user, prod_id):
    product = Products.objects.get(id=prod_id)
    if product.need_enter_price:
        msg = bot.send_message(chat_id=chat_id, text='Введите сумму, на которую хотите пополнить в рублях',
                               reply_markup=buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user, False, product)
    else:
        amount = product.price
        order = create_order(user=user, amount=amount, total_amount=amount, product=product)
        text = f'У вас к оплате {amount}м$. Выберите способ оплаты'
        bot.send_message(chat_id=chat_id, text=text,
                         reply_markup=buttons.payment_method(order_id=order.id, need_enter_new_amount=False))


def change_payment_method(chat_id, order_id):
    order = Order.objects.get(id=order_id)
    text = f'У вас к оплате {order.total_product_price}₽. Выберите новый способ оплаты'
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
    bot.send_message(chat_id=chat_id, text='Ожидайте. Скоро с вами свяжется менеджер для выполнения вашего заказа. Если хотите что-то узнать - напишите в чат с ботом', reply_markup=buttons.go_to_menu())


def callback(data, user, chat_id):
    if data[0] == 'buy':
        buy_step_one(chat_id=chat_id, prod_id=data[1], user=user)
    elif data[0] == 'top_up':
        msg = bot.send_message(chat_id=chat_id, text='Введите сумму, на которую хотите пополнить в рублях',
                               reply_markup=buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user)
    elif data[0] == 'enter_new_amount':
        msg = bot.send_message(chat_id=chat_id, text='Введите сумму, на которую хотите пополнить в рублях',
                               reply_markup=buttons.go_to_menu())
        bot.register_next_step_handler(msg, tup_up_balance, chat_id, user)
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
