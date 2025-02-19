import os

import django
from telebot import types

import buttons
from const import bot

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PayUlimitedBot.settings')
django.setup()
from app.models import Client, BotText


def get_enteties(a):
    entities = []
    for entity in a.split('|')[:-1]:
        n = eval(entity)
        entities.append(
            types.MessageEntity(type=n['type'], offset=n['offset'], length=n['length'], url=n['url'],
                                language=n['language'], custom_emoji_id=n['custom_emoji_id']))
    return entities


def send_text(param, chat_id, markup=None):
    global_text, _ = BotText.objects.get_or_create(name=param)
    params = global_text.text.split('\t\t\t')
    ln = len(params)
    user = Client.objects.get(chat_id=chat_id)
    if user.is_admin:
        markup = buttons.edit_text(markup=markup, param=param)
    text = params[0]
    type = 'text'
    entities = []
    media = None
    if ln == 2 and ('video' in params[1] or 'photo' in params[1]):
        type = params[1].split('_')[0]
        media = params[1].split('_')[1]
    elif ln == 2:
        entities = get_enteties(params[1])
    elif ln == 3:
        type = params[1].split('_')[0]
        entities = get_enteties(params[1])
        media = params[2].split('_')[1]
    if type == 'text':
        return bot.send_message(chat_id=chat_id, text=text, entities=entities, reply_markup=markup)
    elif type == 'photo':
        try:
            return bot.send_photo(chat_id=chat_id, photo=media, caption=text, caption_entities=entities,
                                  reply_markup=markup)
        except Exception as ex:
            return bot.send_message(chat_id=chat_id, text='Главное меню', reply_markup=markup)
    elif type == 'video':
        try:
            return bot.send_video(chat_id=chat_id, photo=media, caption=text, caption_entities=entities,
                                  reply_markup=markup)
        except Exception as ex:
            return bot.send_message(chat_id=chat_id, text='Главное меню', reply_markup=markup)
