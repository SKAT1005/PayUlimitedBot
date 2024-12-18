import buttons
from app.models import Cripto, Order, Manager, Products, Text
from const import bot


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
    context = {
        'usdt_course': usdt_course,
        'status': status,
        'chat': chat,
        'order_history': order_history,
        'managers': managers,
        'products': products
    }
    return context


def get_new_order(manager):
    order = Order.objects.filter(status='wait_manager').order_by('texts__time').first()
    if order:
        order.manager = manager
        order.status = 'dialog_with_manager'
        order.save(update_fields=['manager', 'status'])
        return order.id
    return None


def send_message(request):
    chat_id = request.POST.get('order_id')
    text = request.POST.get('text')
    if text:
        order = Order.objects.get(id=chat_id)
        client = order.client
        Text.objects.create(sender='manager', text=text, order=order)
        n = client.order_id
        if client.order_id == str(order.id):
            bot.send_message(chat_id=order.client.chat_id, text=text)
        else:
            bot.send_message(client.chat_id, 'Вам пришел ответ от менеджера', reply_markup=buttons.go_to_chat(order.id))


def change_order(request):
    pass


def send_to_friend(request):
    pass


def close_order(request):
    pass


def top_down_balance(request):
    pass