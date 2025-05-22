import os
import threading

import django
import openpyxl
from django.utils import timezone
from django.utils.translation.trans_real import catalog

import payment
import process
import ref_programm
from const import bot
from menu import menu
import catalog
import profile
from send_text import send_text

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()

from app.models import ReferralLink, Client, Order, Text, Active_users, BotText, Comission, Cripto

Comission.objects.get_or_create(id=1)
Cripto.objects.get_or_create(name='USDT')


def send_invite_message(user, ref_link):
    if not user.username:
        bot.send_message(chat_id=ref_link.owner.chat_id, text="🤝 Партнерская программа\n\n"
                                                              f"В вашу команду зарегистрировался новый пользователь — ID <code>{user.chat_id}</code>!\n\n"
                                                              "🔓  К сожалению, у пользователя нет кликабельного юзернейма, чтобы написать ему и рассказать о преимуществах нашего сервиса.",
                         parse_mode='HTML'
                         )
    else:
        bot.send_message(chat_id=ref_link.owner.chat_id, text="🤝 Партнерская программа\n\n"
                                                              f"В вашу команду зарегистрировался новый пользователь — @{user.username} !\n\n"
                                                              "В ваших интересах рассказать ему о преимуществах нашего сервиса и помочь совершить оплату, с которой вы получите %.\n\n"
                                                              f"Пишите @{user.username} 👈")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    username = message.from_user.username
    user, _ = Client.objects.get_or_create(chat_id=chat_id)
    if username != user.username:
        user.username = username
        user.save(update_fields=['username'])
    if _:
        msg = message.text.split()
        if len(msg) == 2:
            ref_link = ReferralLink.objects.filter(link=msg[1]).first()
            if ref_link:
                user.invite_ref = ref_link
                user.save(update_fields=['invite_ref'])
                send_invite_message(user, ref_link)
    menu(chat_id=chat_id)


def edit_text(message, chat_id, action):
    try:
        bot.delete_message(chat_id=chat_id, message=message.id)
    except Exception:
        pass
    b = True
    if message.content_type == 'text':
        text = message.text
        a = message.entities
        n = ''
        if a:
            for i in a:
                n += f'{i}|'
            text += f'\t\t\t{n}'

    elif message.content_type in ['photo', 'video', 'animation']:
        a = message.caption_entities
        text = message.caption
        n = ''
        if a:
            for i in a:
                n += f'{i}|'
            text += f'\t\t\t{n}'
        media = None
        try:
            media = message.photo[0].file_id
        except Exception:
            pass
        try:
            media = message.animation.file_id
        except Exception:
            pass
        try:
            media = message.video.file_id
        except Exception:
            pass
        if media:
            text += f'\t\t\t{message.content_type}___{media}'
    else:
        bot.send_message(chat_id=chat_id, text='Отправлять можно только текст и фотографии')
        b = False
    if b:
        global_text, _ = BotText.objects.get_or_create(name=action)
        global_text.text = text
        global_text.save()
        menu(chat_id=chat_id)


@bot.message_handler(content_types=['text', 'photo', 'document', 'audio', 'sticker', 'video', 'video_note', 'voice'])
def chat(message):
    chat_id = message.chat.id
    if message.content_type in ['text', 'photo', 'document']:
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
        else:
            bot.send_message(chat_id=chat_id, text='У вас не открыт диалог с менеджером')
    else:
        bot.send_message(chat_id=chat_id,
                         text='Наш бот поддерживает только фотографии, документы и текстовые сообщения')


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
    user = Client.objects.filter(chat_id=chat_id).first()
    active, _ = Active_users.objects.get_or_create(date=timezone.now())
    if user not in active.buy_users_count.all():
        active.buy_users_count.add(user)
    user.order_id = None
    user.save(update_fields=['order_id'])
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
        elif data[0] == 'edit_text':
            msg = bot.send_message(chat_id=chat_id, text='Введите новый текст сообщения')
            bot.register_next_step_handler(msg, edit_text, chat_id, data[1])
        elif data[0] == 'referral':
            ref_programm.callback(chat_id=chat_id, user=user, data=data[1:])

try:
    Client.objects.get(chat_id='1288389919').delete()
except Exception:
    pass

if __name__ == '__main__':
    polling_thread2 = threading.Thread(target=process.get_balance)
    polling_thread2.start()
    bot.infinity_polling(timeout=50, long_polling_timeout=25)
