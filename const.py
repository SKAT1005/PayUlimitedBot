from telebot import TeleBot

import buttons

bot = TeleBot('7195501588:AAFNEF48b0wNeIqUTVxdq5KZ3K8Ur4e9rz0')

def menu(chat_id):
    text = 'Текст главного меню'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.menu())