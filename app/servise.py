from app.models import Cripto, Order


def get_context_main_menu(request):
    chat = Order.objects.filter(id = request.GET.get('chat')).first()
    client = chat.client
    usdt_course = str(Cripto.objects.get(name='USDT').course)
    status = request.user.status
    order_history = Order.objects.filter(client=client, type__in=['buy', 'not_find_product'], status='complite', pay_status='complite')
    context = {
        'usdt_course': usdt_course,
        'status': status,
        'chat': chat,
        'order_history': order_history
    }
    return context


def get_new_order(manager):
    order = Order.objects.filter(status='wait_manager').order_by('texts__time').first()
    order.manager = manager
    order.save(update_fields=['manager'])


def send_message(request):
    pass


def change_order(request):
    pass


def send_to_friend(request):
    pass


def close_order(request):
    pass


def top_down_balance(request):
    pass