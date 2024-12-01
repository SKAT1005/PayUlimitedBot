import os

import django
from django.utils.translation.trans_real import catalog

import payment
from const import bot
from menu import menu
import catalog
import profile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from app.models import ReferralLink, Client


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user, _ = Client.objects.get_or_create(chat_id=chat_id)
    if _:
        msg = message.text.split()
        if len(msg) == 2:
            ref_link = ReferralLink.objects.filter(link=msg[1])
            user.invite_ref = ref_link
            user.save(update_fields=['invite_ref'])
    menu(chat_id=chat_id)


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

bot.polling(none_stop=True)