import base64
import os

import django
from django.db.models import TextField
from django.utils import timezone
from django.utils.translation.trans_real import catalog

import payment
from const import bot
from menu import menu
import catalog
import profile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from app.models import ReferralLink, Client, Order, Text


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user, _ = Client.objects.get_or_create(chat_id=chat_id, username=message.from_user.username)
    if _:
        msg = message.text.split()
        if len(msg) == 2:
            ref_link = ReferralLink.objects.filter(link=msg[1])
            user.invite_ref = ref_link
            user.save(update_fields=['invite_ref'])
    menu(chat_id=chat_id)


@bot.message_handler(content_types=['text', 'photo', 'document'])
def chat(message):
    chat_id = message.chat.id
    client = Client.objects.get(chat_id=chat_id)
    if client.order_id:
        order = Order.objects.get(id=client.order_id)
        order.last_message_time = timezone.now()
        order.save(update_fields=['last_message_time'])
        if order.status == 'chat_with_friend':
            order.status = 'wait_manager'
            order.save(update_fields=['status'])
        if message.content_type == 'text':
            Text.objects.create(order=order, text=message.text, sender='client')
        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            Text.objects.create(order=order, file_id=file_id, is_photo=True, is_text=False, sender='client')
        else:
            file_id = message.document.file_id
            Text.objects.create(order=order, file_id=file_id, is_pdf=True, is_text=False, sender='client')
        order.have_new_message = True
        order.save(update_fields=['have_new_message'])

def go_to_chat(chat_id, user, order_id):
    user.order_id = order_id
    user.save(update_fields=['order_id'])
    order = Order.objects.get(id=order_id)
    text = ''
    for message in order.texts.all():
        if message.is_text:
            text += f'{message.sender}: {message.text}\n'
    if text:
        bot.send_message(chat_id=chat_id, text=text.replace('manager', 'Менеджер').replace('client', 'Вы'))




@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    user, _ = Client.objects.get_or_create(chat_id=chat_id)
    if call.message:
        data = call.data.split('|')
        bot.clear_step_handler_by_chat_id(chat_id=chat_id)
        if data[0] != 'chat':
            bot.delete_message(chat_id=chat_id, message_id=call.message.id)
        if data[0] == 'menu':
            menu(chat_id=chat_id)
        elif data[0] == 'catalog':
            catalog.callback(data=data[1:], chat_id=chat_id, user=user)
        elif data[0] == 'profile':
            profile.callback(data=data[1:], chat_id=chat_id, user=user)
        elif data[0] == 'payment':
            payment.callback(data=data[1:], chat_id=chat_id, user=user)
        elif data[0] == 'go_to_chat':
            go_to_chat(chat_id=chat_id, user=user, order_id=data[1])
        elif data[0] == 'manager_chat':
            catalog.create_order(chat_id, user, 'other')


bot.polling(none_stop=True)
