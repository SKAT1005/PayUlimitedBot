import buttons
from send_text import send_text





def menu(chat_id):
    send_text('catalog_list', chat_id, buttons.menu())