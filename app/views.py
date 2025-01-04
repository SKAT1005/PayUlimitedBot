import decimal
from io import BytesIO

import openpyxl
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from django.views import View
from .servise import get_context_main_menu, get_new_order, send_message, change_order, send_to_friend, close_order, \
    top_down_balance, get_context_profile, service_mailing, log_manager_action, send_manager, statistics
from .state import *


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Попытка аутентификации пользователя
        user = authenticate(request, username=username, password=password)

        if user is not None and isinstance(user, Manager):
            login(request, user)
            log_manager_action(user, 'Вошел в систему')
            return redirect('main')  # Замените 'home' на вашу страницу после входа
        else:
            # Если логин или пароль неверные
            messages.error(request, 'Неверный логин или пароль.')

    return render(request, 'login.html')


class MainView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        context = get_context_main_menu(request)
        return render(request, 'main.html', context=context)

    def post(self, request):
        manager = request.user
        chat_id = request.POST.get('order_id')
        if not manager.is_authenticated:
            return redirect('login')
        if 'new_order' in request.POST:
            log_manager_action(manager, 'Взял новый заказ')
            chat_id = get_new_order(manager)
            if not chat_id:
                return HttpResponseRedirect(reverse('main'))
        elif 'send_message' in request.POST:
            log_manager_action(manager, 'Отправил пользователю сообщение')
            send_message(request)
        elif 'change_order' in request.POST:
            log_manager_action(manager, f'Внес изменения в заказ номер {request.POST.get("order_id")}')
            change_order(request)
        elif 'send_to_friend' in request.POST:
            log_manager_action(manager, f'Отправил заказ номер {request.POST.get("order_id")} в отдел заботы')
            send_to_friend(request)
            return redirect('main')
        elif 'close_order' in request.POST:
            log_manager_action(manager, f'Закрыл заказ номер {request.POST.get("order_id")}')
            close_order(request)
            return redirect('login')
        elif 'top_down_balance' in request.POST:
            log_manager_action(manager,
                               f'Списал средства с баланса пользователя по заказу номер {request.POST.get("order_id")}')
            top_down_balance(request)
        elif 'send_manager' in request.POST:
            log_manager_action(manager, f'Отправил заказ номер {request.POST.get("order_id")} менеджерам')
            send_manager(request)
            return redirect('main')
        return HttpResponseRedirect(reverse('main') + f'?chat={chat_id}')


@login_required
def get_messages(request):
    chat_id = request.GET.get('chat')
    order = Order.objects.get(id=chat_id)
    has_new = order.have_new_message
    return JsonResponse({'newMessages': has_new})


def change_status(request):
    if not request.user.is_authenticated:
        return redirect('login')
    manager = request.user
    log_manager_action(manager, 'Изменил статус онлайна')
    manager.status = request.GET.get('status')
    manager.save(update_fields=['status'])
    return redirect('main')


class MailingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_friend:
                products = Products.objects.all()
                context = {'products': products}
                return render(request, 'mailing.html', context=context)
            else:
                return redirect('main')
        else:
            return redirect('login')

    def post(self, request):
        log_manager_action(request.user, 'Отправил рассылку пользователям')
        service_mailing(request)
        return redirect('mailing')


class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        log_manager_action(request.user, 'Зашел на страницу профиля')
        context = get_context_profile(request.user)
        return render(request, 'profile.html', context=context)

    def post(self, request):
        manager_id = request.POST.get('manager_id')
        manager = Manager.objects.get(id=manager_id)
        top_down_balance = decimal.Decimal(request.POST.get('top_down_balance'))
        manager.commission_balance -= top_down_balance
        manager.save(update_fields=['commission_balance'])
        return redirect('profile')



class StatisticsView(View):

    def get(self, request):
        return render(request, 'statistics.html',)

    def post(self, request):

        wb = statistics(request)
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(buffer.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Статистика.xlsx"'
        return response