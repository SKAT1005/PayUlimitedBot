import buttons
from const import bot

def menu(chat_id):
    text = 'Добро пожаловать в Pay Unlimited!\n' \
           'Мы поможем оплатить подписки на зарубежные сервисы недоступные в России.\n' \
           'Выберите нужный раздел:'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.menu())