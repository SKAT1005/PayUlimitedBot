import buttons
from const import bot

def menu(chat_id):
    text = 'Текст главного меню'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.menu())