from datetime import datetime

import buttons
from app.models import Order
from const import bot

from send_text import send_text


def profile(chat_id, user):
    text = f'Добро пожаловать в ваш личный кабинет! 🎉\n' \
           f'Здесь вы можете ознакомится с историей ваших покупок, а так же пополнить баланс\n' \
           f'Ваш баланс: {user.balance}'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.profile())


def history_list(chat_id, user, page):
    markup = buttons.history(page=page, user=user)
    send_text('history_list', chat_id, markup)


def history_detail(chat_id, page, history_id):
    history = Order.objects.get(id=history_id)
    date = history.time
    date_string = f'{date.day}.{date.month}.{date.year} {date.hour}:{date.minute}'
    text = f'Название товара: {history.name}\n' \
           f'Сумма оплаты: {history.total_product_price_str}\n' \
           f'Способ оплаты: {history.payment_type}\n' \
           f'Дата покупки: {date_string}'
    markup = buttons.history_detail(page)
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def callback(data, user, chat_id):
    if len(data) == 0:
        profile(chat_id=chat_id, user=user)
    elif data[0] == 'history':
        history_list(chat_id=chat_id, page=data[1], user=user)
    elif data[0] == 'history_detail':
        history_detail(chat_id=chat_id, page=data[2], history_id=data[1])
