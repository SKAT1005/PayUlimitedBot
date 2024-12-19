import datetime
import decimal

import buttons
from app.models import Cripto, Order, Manager, Products, Text, Client, ManagerActions
from const import bot


def log_manager_action(manager, action):
    ManagerActions.objects.create(manager=manager, action=action)

def get_context_main_menu(request):
    try:
        chat = Order.objects.filter(id = request.GET.get('chat')).first()
        chat.have_new_message = False
        chat.save(update_fields=['have_new_message'])
        client = chat.client
        order_history = Order.objects.filter(client=client, type__in=['buy', 'not_find_product'], status='complite',
                                             pay_status='complite')
        n = len(order_history)
        n = max(n-5, 0)
        order_history = order_history[n:]
    except Exception as e:
        chat = None
        order_history = []
    usdt_course = str(Cripto.objects.get(name='USDT').course)
    status = request.user.status
    managers = Manager.objects.filter(is_friend=False)
    products = Products.objects.all()
    if request.user.is_friend:
        manager_chats = Order.objects.filter(status='chat_with_friend')
    else:
        manager_chats = request.user.orders_for_manager.filter(status='dialog_with_manager').order_by('-last_message_time')
    context = {
        'manager_chats': manager_chats,
        'usdt_course': usdt_course,
        'status': status,
        'chat': chat,
        'order_history': order_history,
        'managers': managers,
        'products': products
    }
    return context


def get_new_order(manager):
    order = Order.objects.filter(status='wait_manager').order_by('last_message_time').first()
    if order:
        order.manager = manager
        order.status = 'dialog_with_manager'
        order.save(update_fields=['manager', 'status'])
        return order.id
    return None

def send_manager(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    order.status = 'wait_manager'
    order.save(update_fields=['status'])

def send_message(request):
    chat_id = request.POST.get('order_id')
    text = request.POST.get('text')
    if text:
        order = Order.objects.get(id=chat_id)
        client = order.client
        Text.objects.create(sender='manager', text=text, order=order)
        if client.order_id == str(order.id):
            try:
                bot.send_message(chat_id=order.client.chat_id, text=text)
            except Exception:
                pass
        else:
            try:
                bot.send_message(client.chat_id, 'Вам пришел ответ от менеджера', reply_markup=buttons.go_to_chat(order.id))
            except Exception:
                pass


def change_order(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    client = order.client
    if order.type == 'buy':
        comment = request.POST.get('comment')
        card_holder_id = request.POST.get('card_holder_id')
        pay_status = request.POST.get('pay_status')
        date = request.POST.get('date')
        client.comment = comment
        order.card_holder_id = card_holder_id
        order.pay_status = pay_status
        if date:
            order.date = date
        order.save(update_fields=['card_holder_id', 'pay_status', 'date'])
        client.save(update_fields=['comment'])
    elif order.type == 'top_up':
        comment = request.POST.get('comment')
        product_price = request.POST.get('product_price')
        total_product_price = request.POST.get('total_product_price')
        payment_type = request.POST.get('payment_type')
        pay_status = request.POST.get('pay_status')
        client.comment = comment
        order.pay_status = pay_status
        order.product_price = product_price
        order.total_product_price = total_product_price
        order.payment_type = payment_type
        order.save(update_fields=['pay_status', 'product_price', 'total_product_price', 'payment_type'])
        client.save(update_fields=['comment'])
    elif order.type == 'not_find_product':
        comment = request.POST.get('comment')
        name = request.POST.get('name')
        product_price = request.POST.get('product_price')
        total_product_price = request.POST.get('total_product_price')
        payment_type = request.POST.get('payment_type')
        card_holder_id = request.POST.get('card_holder_id')
        pay_status = request.POST.get('pay_status')
        date = request.POST.get('date')
        client.comment = comment
        if not Products.objects.filter(name=name):
            Products.objects.create(name=name)
        order.name = name
        order.product_price = product_price
        order.total_product_price = total_product_price
        order.payment_type = payment_type
        order.card_holder_id = card_holder_id
        order.pay_status = pay_status
        if date:
            order.date = date
        order.save(update_fields=['name', 'product_price', 'total_product_price', 'payment_type', 'card_holder_id', 'pay_status', 'date'])
        client.save(update_fields=['comment'])
    else:
        comment = request.POST.get('comment')
        type = request.POST.get('type')
        client.comment = comment
        order.type = type
        order.save(update_fields=['type'])
        client.save(update_fields=['comment'])



def send_to_friend(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    order.manager = None
    order.status = 'chat_with_friend'
    order.save(update_fields=['status', 'manager'])


def close_order(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    manager = order.manager
    order.status = 'complite'
    order.save(update_fields=['status'])
    change_order(request)
    if order.type in ('buy', 'not_find_product'):
        if order.pay_status == 'complite':
            manager.commission_balance += decimal.Decimal(float(order.total_product_price)*0.1)
            manager.save(update_fields=['commission_balance'])
            card_holder = Manager.objects.filter(id=order.card_holder_id).first()
            card_holder.commission_balance += decimal.Decimal(float(order.total_product_price)*0.1)
            card_holder.save(update_fields=['commission_balance'])
    elif order.type == 'top_up':
        if order.pay_status == 'complite':
            client = order.client
            client.balance += decimal.Decimal(order.product_price)
            client.save(update_fields=['balance'])
            try:
                bot.send_message(chat_id=client.chat_id, text=f'Ваш баланс успешно пополнен на {order.product_price}$', reply_markup=buttons.go_to_menu())
            except Exception:
                pass




def top_down_balance(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    client = order.client
    if client.balance >= order.total_product_price:
        client.balance -= order.total_product_price
        client.save(update_fields=['balance'])
        order.pay_status = 'pay_complite'
        order.save(update_fields=['pay_status'])
    else:
        order.pay_status = 'faild_pay'
        order.save(update_fields=['pay_status'])


def get_context_profile(manager):
    list = {}
    if not manager.is_staff:
        orders_manager = Order.objects.filter(manager=manager, type__in=['buy', 'not_find_product'], pay_status='complite', status='complite')
        orders_card_holder = Order.objects.filter(card_holder_id=manager.id, pay_status='complite', status='complite')
        for order in orders_manager:
            date = f'{order.time.date()}'
            if date in list:
                list[date]['manager'] += round(float(order.total_product_price)*0.1, 2)
                list[date]['total'] += round(float(order.total_product_price)*0.1, 2)
            else:
                list[date] = {'manager': 0, 'total': 0, 'card_holder': 0}
                list[date]['manager'] = round(float(order.total_product_price)*0.1, 2)
                list[date]['total'] = round(float(order.total_product_price)*0.1, 2)

        for order in orders_card_holder:
            date = f'{order.time.date()}'
            if date in list:
                list[date]['card_holder'] += round(float(order.total_product_price)*0.1, 2)
                list[date]['total'] += round(float(order.total_product_price)*0.1, 2)
            else:
                list[date] = {'manager': 0, 'total': 0, 'card_holder': 0}
                list[date]['card_holder'] += round(float(order.total_product_price)*0.1, 2)
                list[date]['total'] = round(float(order.total_product_price)*0.1, 2)
        commission_list = []
        for i in list:
            commission_list.append({
                'date': i,
                'manager': list[i]['manager'],
                'card_holder': list[i]['card_holder'],
                'total': list[i]['total']
            })
        return {'commissions': commission_list}
    else:
        return {'managers': Manager.objects.filter(is_friend=False, is_staff=False)}



def service_mailing(request):
    if request.POST.get('mail_type') == 'all':
        text = request.POST.get('text')
        clients = Client.objects.all()
    else:
        date_str = request.POST.get('date')
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        product = request.POST.get('product')
        text = request.POST.get('text')
        clients_with_purchases_before = Client.objects.filter(
            orders_for_user__type__in=['buy', 'not_find_product'],
            orders_for_user__pay_status='complite',
            orders_for_user__name=product,
            orders_for_user__time__lte=date
        )

        # Исключаем из них клиентов, у которых есть заказы типа 'buy' с указанным продуктом после cutoff_datetime
        clients = clients_with_purchases_before.exclude(
            orders_for_user__type__in=['buy', 'not_find_product'],
            orders_for_user__pay_status='complite',
            orders_for_user__name=product,
            orders_for_user__time__gt=date
        ).distinct()
    for client in clients:
        try:
            bot.send_message(chat_id=client.chat_id, text=text)
        except Exception:
            pass


