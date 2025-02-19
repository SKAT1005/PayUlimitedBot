import datetime
import decimal

import openpyxl
from django.http import HttpResponse

import buttons
from app.models import Cripto, Order, Manager, Products, Text, Client, ManagerActions
from const import bot
from .state import *


def log_manager_action(manager, action):
    ManagerActions.objects.create(manager=manager, action=action)


def get_context_main_menu(request):
    try:
        chat = Order.objects.filter(id=request.GET.get('chat')).first()
        chat.have_new_message = False
        chat.save(update_fields=['have_new_message'])
        client = chat.client
        order_history = Order.objects.filter(client=client)
        n = len(order_history)
        n = max(n - 5, 0)
        order_history = order_history[n:]
    except Exception as e:
        chat = None
        order_history = []
    usdt_course = str(Cripto.objects.get(name='USDT').course)
    status = request.user.status
    managers = Manager.objects.filter(is_friend=False)
    products = Products.objects.all()
    untake_order = Order.objects.filter(status='wait_manager').count()
    if request.user.is_friend:
        manager_chats = Order.objects.filter(status='chat_with_friend')
    else:
        manager_chats = request.user.orders_for_manager.filter(status='dialog_with_manager').order_by(
            '-last_message_time')
    context = {
        'manager_chats': manager_chats,
        'usdt_course': usdt_course,
        'status': status,
        'chat': chat,
        'order_history': order_history,
        'managers': managers,
        'products': products,
        'untake_order': untake_order
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
                bot.send_message(client.chat_id, 'Вам пришел ответ от менеджера',
                                 reply_markup=buttons.go_to_chat(order.id))
            except Exception:
                pass


def change_order(request):
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    client = order.client
    if order.type == 'buy':
        balance = request.POST.get('balance')
        client.balance = decimal.Decimal(balance)
        client.save(update_fields=['balance'])
        comment = request.POST.get('comment')
        card_holder_id = request.POST.get('card_holder_id')
        pay_status = request.POST.get('pay_status')
        date = request.POST.get('date')
        client.comment = comment
        order.card_holder_id = card_holder_id
        order.pay_status = pay_status
        if date:
            order.date = date
            order.save(update_fields=['date'])
        if date:
            Order.objects.create(
                client=client,
                name=order.name,
                product_price=order.product_price,
                total_product_price=order.total_product_price,
                payment_type=order.payment_type,
                pay_status=pay_status,
                status='chat_with_friend',
                date=date
            )
        order.save(update_fields=['card_holder_id', 'pay_status'])
        client.save(update_fields=['comment'])
    elif order.type == 'top_up':
        balance = request.POST.get('balance')
        client.balance = decimal.Decimal(balance)
        client.save(update_fields=['balance'])
        comment = request.POST.get('comment')
        product_price = decimal.Decimal(request.POST.get('product_price'))
        total_product_price = decimal.Decimal(request.POST.get('total_product_price'))
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
        balance = request.POST.get('balance')
        client.balance = decimal.Decimal(balance)
        client.save(update_fields=['balance'])
        comment = request.POST.get('comment')
        name = request.POST.get('name')
        product_price = decimal.Decimal(request.POST.get('product_price'))
        total_product_price = decimal.Decimal(request.POST.get('total_product_price'))
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
            order.save(update_fields=['date'])
        if date:
            Order.objects.create(
                client=client,
                name=name,
                product_price=product_price,
                total_product_price=total_product_price,
                payment_type=payment_type,
                pay_status=pay_status,
                status='chat_with_friend',
                date=date
            )
        order.save(update_fields=['name', 'product_price', 'total_product_price', 'payment_type', 'card_holder_id',
                                  'pay_status'])
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


def count_ref(order, client):
    link = client.invite_ref
    ref = link.owner
    if client.stay_old or client.stay_new:
        link.old_user_buy.add(order)
    else:
        link.new_user_buy.add(order)
        link.last_invite_buyer_user_time = timezone.now()
        link.save(update_fields=['last_invite_buyer_user_time'])
    if ref.referral_status == 'start':
        if 1 <= order.product_price <= 20:
            percent = round(order.product_price * 0.04, 2)
        elif 21 <= order.product_price <= 50:
            percent = round(order.product_price * 0.027, 2)
        else:
            percent = round(order.product_price * 0.018, 2)
    elif ref.referral_status == 'cool':
        if 1 <= order.product_price <= 20:
            percent = round(order.product_price * 0.05, 2)
        elif 21 <= order.product_price <= 50:
            percent = round(order.product_price * 0.032, 2)
        else:
            percent = round(order.product_price * 0.023, 2)
    ref.balance += decimal.Decimal(percent)
    ref.save(update_fields=['balance'])
    link.money += decimal.Decimal(percent)
    ref.save(update_fields=['money'])


def close_order(request):
    change_order(request)
    order_id = request.POST.get('order_id')
    order = Order.objects.get(id=order_id)
    manager = order.manager
    order.status = 'complite'
    order.close_time = timezone.now()
    order.save(update_fields=['status', 'close_time'])
    client = order.client
    if order.type in ('buy', 'not_find_product'):
        if order.pay_status == 'complite':
            if client.invite_ref:
                count_ref(order=order, client=client)
            for mail in client.mailing.all():
                if mail.date >= timezone.now() - timedelta(days=3):
                    mail.buy_users += 1
                    mail.buy_summ += order.total_product_price
                    mail.save(update_fields=['buy_users', 'buy_summ'])
                client.mailing.remove(mail)
            if not client.stay_new:
                client.stay_new = timezone.now()
                client.save(update_fields=['stay_new'])
            else:
                if not client.stay_old:
                    client.stay_old = timezone.now()
                    client.save(update_fields=['stay_old'])
            active, _ = Active_users.objects.get_or_create(date=timezone.now())
            active.buy_users_count.add(client)
            manager.commission_balance += decimal.Decimal(float(order.total_product_price) * 0.1)
            manager.save(update_fields=['commission_balance'])
            card_holder = Manager.objects.filter(id=order.card_holder_id).first()
            card_holder.commission_balance += decimal.Decimal(float(order.total_product_price) * 0.1)
            card_holder.save(update_fields=['commission_balance'])
    elif order.type == 'top_up':
        if order.pay_status == 'complite':
            client.balance += decimal.Decimal(order.product_price)
            client.save(update_fields=['balance'])
            try:
                bot.send_message(chat_id=client.chat_id, text=f'Ваш баланс успешно пополнен на {order.product_price}$',
                                 reply_markup=buttons.go_to_menu())
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
        orders_manager = Order.objects.filter(manager=manager, type__in=['buy', 'not_find_product'],
                                              pay_status='complite', status='complite')
        orders_card_holder = Order.objects.filter(card_holder_id=manager.id, pay_status='complite', status='complite')
        for order in orders_manager:
            date = f'{order.time.date()}'
            if date in list:
                list[date]['manager'] += round(float(order.total_product_price) * 0.1, 2)
                list[date]['total'] += round(float(order.total_product_price) * 0.1, 2)
            else:
                list[date] = {'manager': 0, 'total': 0, 'card_holder': 0}
                list[date]['manager'] = round(float(order.total_product_price) * 0.1, 2)
                list[date]['total'] = round(float(order.total_product_price) * 0.1, 2)

        for order in orders_card_holder:
            date = f'{order.time.date()}'
            if date in list:
                list[date]['card_holder'] += round(float(order.total_product_price) * 0.1, 2)
                list[date]['total'] += round(float(order.total_product_price) * 0.1, 2)
            else:
                list[date] = {'manager': 0, 'total': 0, 'card_holder': 0}
                list[date]['card_holder'] += round(float(order.total_product_price) * 0.1, 2)
                list[date]['total'] = round(float(order.total_product_price) * 0.1, 2)
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
    mail = Mailing.objects.create(text=text)
    for client in clients:
        try:
            bot.send_message(chat_id=client.chat_id, text=text)
            client.mailing.add(mail)
            mail.send_users += 1
            mail.save(update_fields=['send_users'])
        except Exception:
            pass


def statistics(request):
    wb = openpyxl.Workbook()

    startdate = request.POST.get('startdate')
    enddate = request.POST.get('enddate')

    if request.POST.get('heart_map') == 'on':
        heart_map(wb)
    if request.POST.get('revenue_structure') == 'on':
        revenue_structure(wb, startdate, enddate)
    if request.POST.get('statistics_for_each_service') == 'on':
        statistics_for_each_service(wb, startdate, enddate)
    if request.POST.get('deal_stats') == 'on':
        deal_stats(wb, startdate, enddate)
    if request.POST.get('mailing_stats') == 'on':
        mailing_stats(wb, startdate, enddate)
    if request.POST.get('conversion') == 'on':
        conversion(wb, startdate, enddate)
    if request.POST.get('active_users') == 'on':
        active_users(wb, startdate, enddate)
    if request.POST.get('balance_stat') == 'on':
        balance_stat(wb, startdate, enddate)
    if request.POST.get('expenses_stats') == 'on':
        expenses_stats(wb, startdate, enddate)
    if request.POST.get('link_stats') == 'on':
        link_state(wb)
    if request.POST.get('traffic_state') == 'on':
        traffic_state(wb, startdate, enddate)
    return wb
