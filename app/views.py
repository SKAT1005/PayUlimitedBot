from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from django.views import View
from .models import Cripto, Manager
from .servise import get_context_main_menu, get_new_order, send_message, change_order, send_to_friend, close_order, \
    top_down_balance


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
        return render(request,'main.html', context=context)

    def post(self, request):
        manager = request.user
        chat_id = request.POST.get('order_id')
        if not manager.is_authenticated:
            return redirect('login')
        if 'new_order' in request.POST:
            chat_id = get_new_order(manager)
            if not chat_id:
                return HttpResponseRedirect(reverse('main'))
        elif 'send_message' in request.POST:
            send_message(request)
        elif 'change_order' in request.POST:
            change_order(request)
        elif 'send_to_friend' in request.POST :
            send_to_friend(request)
        elif 'close_order' in request.POST:
            close_order(request)
        elif 'top_down_balance' in request.POST:
            top_down_balance(request)
        return HttpResponseRedirect(reverse('main') + f'?chat={chat_id}')


def change_status(request):
    if not request.user.is_authenticated:
        return redirect('login')
    manager = request.user
    manager.status = request.GET.get('status')
    manager.save(update_fields=['status'])
    return redirect('main')


class MailingView(View):
    def get(self, request):
        return render(request,'mailing.html')



class ProfileView(View):
    def get(self, request):
        return render(request,'profile.html')
