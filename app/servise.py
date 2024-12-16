from app.models import Cripto, Order, Manager, Products, Text
from const import bot


def get_context_main_menu(request):
    try:
        chat = Order.objects.filter(id = request.GET.get('chat')).first()
        client = chat.client
        order_history = Order.objects.filter(client=client, type__in=['buy', 'not_find_product'], status='complite',
                                             pay_status='complite')
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
    order = Order.objects.get(id=chat_id)
    Text.objects.create(sender='manager', text=text, order=order)
    bot.send_message(chat_id=order.client.chat_id, text=text)


def change_order(request):
    pass


def send_to_friend(request):
    pass


def close_order(request):
    pass


def top_down_balance(request):
    pass