import buttons
from app.models import Products, Order
from const import bot
from send_text import send_text


def catalog_list(chat_id, page, param, name=None):
    markup = buttons.catalog_list(page=page, param=param, name=name)
    send_text('catalog_list', chat_id, markup)


def filter_name(message, chat_id):
    if message.content_type == 'text':
        name = message.text
        catalog_list(chat_id=chat_id, page=1, param='name', name=name)
    else:
        msg = send_text('filter_name', chat_id, buttons.go_to_menu())
        bot.register_next_step_handler(msg, filter_name, chat_id)


def prod_detail(chat_id, prod_id, page):
    prod = Products.objects.get(id=prod_id)
    text = f'Название: {prod.name}\n' \
           f'Описание: {prod.description}\n'
    if not prod.need_enter_price:
        text += f'Цена: {prod.price}'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=buttons.prod_detail(page=page, prod_id=prod_id))


def create_order(chat_id, user, type):
    order = Order.objects.create(client=user, type=type, status='wait_manager')
    user.order_id = order.id
    user.save(update_fields=['order_id'])
    send_text('create_order', chat_id)

def callback(data, user, chat_id):
    if data[0] == 'all':
        catalog_list(chat_id=chat_id, page=data[1], param=data[0])
    elif data[0] == 'name':
        catalog_list(chat_id=chat_id, page=data[2], param=data[0], name=data[1])
    elif data[0] == 'name_filter':
        msg = send_text('filter_name', chat_id, buttons.go_to_menu())
        bot.register_next_step_handler(msg, filter_name, chat_id)
    elif data[0] == 'dont_find':
        create_order(chat_id, user, 'not_find_product')
    elif data[0] == 'detail':
        prod_detail(chat_id=chat_id, prod_id=data[1], page=data[2])
