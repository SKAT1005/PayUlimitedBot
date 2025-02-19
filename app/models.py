import base64

from django.contrib.auth.models import AbstractUser, Group, Permission, PermissionsMixin
from django.db import models

from const import bot


class Client(models.Model):
    REF_STATUS = (
        ('start', 'Начинающий рефовод'),
        ('cool', 'Опытный рефовод')
    )
    chat_id = models.CharField(max_length=128, verbose_name='ID чата в телеграмме')
    username = models.CharField(max_length=128, null=True, verbose_name='Ник клиента')
    join_time = models.DateField(auto_now_add=True, verbose_name='Время присоединения')
    mailing = models.ManyToManyField('Mailing', blank=True, verbose_name='Рассылки, которые получил пользователь')
    stay_new = models.DateField(blank=True, null=True, verbose_name='Когда стал новым клиентов')
    stay_old = models.DateField(blank=True, null=True, verbose_name='Когда стал старым клиентом')
    invite_ref = models.ForeignKey('ReferralLink', blank=True, null=True, on_delete=models.PROTECT, related_name='usr',
                                   verbose_name='Ссылка-приглашения')
    comment = models.TextField(default='', blank=True, null=True, verbose_name='Комментарий по клиенту')
    balance = models.DecimalField(default=0, max_digits=100, decimal_places=2, verbose_name='Баланс клиента')
    referral_status = models.CharField(max_length=128, default='start', choices=REF_STATUS)
    order_id = models.CharField(max_length=8, default=None, blank=True, null=True,
                                verbose_name='Id ордера, по которому ведется диалог')
    need_to_pay = models.DecimalField(default=0, max_digits=100, decimal_places=2, verbose_name='Сумма к оплате')

    is_admin = models.BooleanField(default=False, verbose_name='Является ли админом?')

    def __str__(self):
        if self.username:
            return self.username
        return self.chat_id


class ReferralLink(models.Model):
    CATEGORY_CHOICES = (
        ('yt', 'Ютуб'),
        ('vk', 'Вконтакте'),
        ('tk', 'Тикток'),
        ('tv', 'Твитч'),
        ('tg', 'Телеграм'),
        ('ref', 'Реферальная система')
    )
    owner = models.ForeignKey('Client', related_name='referal_links', on_delete=models.CASCADE,
                              verbose_name='Создатель реферальной ссылки')
    name = models.CharField(max_length=128, verbose_name='Имя ссылки')
    type = models.CharField(max_length=32, default='ref', choices=CATEGORY_CHOICES)
    money = models.DecimalField(default=0, max_digits=100, decimal_places=2, verbose_name='Денег получено с ссылки')
    last_invite_buyer_user_time = models.DateTimeField(default=None, blank=True, null=True,
                                                       verbose_name='Время, когда ссылка привела последнего пользователя, который купил что-то')
    link = models.CharField(max_length=128, verbose_name='Ссылка')
    new_user_buy = models.ManyToManyField('Order', related_name='new_user_referrals', blank=True,
                                          verbose_name='Покупки новых пользователей')
    old_user_buy = models.ManyToManyField('Order', related_name='old_user_referrals', blank=True,
                                          verbose_name='Покупки старых пользователей')


class Products(models.Model):
    name = models.CharField(max_length=128, verbose_name='Имя товара')
    description = models.TextField(blank=True, null=True, verbose_name='Описание товара')
    price = models.DecimalField(blank=True, null=True, max_digits=100, decimal_places=2,
                                verbose_name='Цена товара в долларах')
    need_enter_price = models.BooleanField(default=False, verbose_name='Требуется ли ввод цены покупки?')
    in_bot = models.BooleanField(default=False, verbose_name='Требуется ли размещение в боте?')


class Cripto(models.Model):
    name = models.CharField(max_length=8, verbose_name='Название криптовалюты')
    course = models.DecimalField(default=100, max_digits=100, decimal_places=8, verbose_name='Курс криптовалюты')
    dec = models.IntegerField(default=2, verbose_name='Кол-во знаков после запятой')


class Manager(AbstractUser):
    commission_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        verbose_name="Комиссионный баланс"
    )
    status = models.CharField(
        max_length=10,
        choices=[('online', 'Онлайн'), ('offline', 'Офлайн'), ('away', 'Отошел')],
        default='offline',
        verbose_name="Статус"
    )
    is_friend = models.BooleanField(default=False, verbose_name='Является ли сотрудником отдела заботы?')

    def __str__(self):
        return self.username


class Order(models.Model):
    STATUS_CHOICES = (
        ('wait_create', 'Ожидает создания'),
        ('wait_manager', 'Ожидаем ответа менеджера'),
        ('dialog_with_manager', 'Общаемся с менеджером'),
        ('chat_with_friend', 'Направлен в отел заботы'),
        ('complite', 'Завершен'),
    )
    PAY_CHOICES = (
        ('question', 'Уточняющие вопросы'),
        ('say_price', 'Сказал цену'),
        ('send_requisites', 'Скинул реквизиты'),
        ('pay_complite', 'Оплата прошла успешно'),
        ('give_card', 'Дал карту'),
        ('faild_pay', 'На балансе недостаточно средств'),
        ('complite', 'Сделка завершена успешно'),
        ('cansel', 'Сделка не завершена')
    )
    PAYMENT_TYPE_CHOICES = (
        ('bybit', 'Bybit'),
        ('wallet', 'Telegram Wallet'),
        ('card', 'Банковская карта'),
        ('balance', 'Баланс профиля')
    )
    TYPE_CHOICES = (
        ('buy', 'Покупка'),
        ('top_up', 'Пополнение баланса'),
        ('not_find_product', 'Не нашел товар'),
        ('other', 'Другой вопрос')
    )
    manager = models.ForeignKey('Manager', blank=True, null=True, related_name='orders_for_manager',
                                on_delete=models.PROTECT, verbose_name='Менеджер заказа')
    client = models.ForeignKey('Client', related_name='orders_for_user', on_delete=models.PROTECT,
                               verbose_name='Клиент заказа')

    product_price = models.DecimalField(max_digits=10, blank=True, null=True, decimal_places=2,
                                        verbose_name='Цена товара в долларах')
    total_product_price_str = models.CharField(max_length=128, verbose_name='Цена в строке', blank=True)

    total_product_price = models.DecimalField(max_digits=10, blank=True, null=True, decimal_places=2,
                                              verbose_name='Итоговая цена товара')
    name = models.CharField(max_length=128, blank=True, null=True, verbose_name='Название продукта')
    is_first_buy = models.BooleanField(default=False, verbose_name='Первая ли это покупка')

    card_holder_id = models.CharField(max_length=8, blank=True, null=True,
                                      verbose_name='Id менеджера, чей картой производится оплата')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='wait_create',
                              verbose_name='Статус заказа')
    pay_status = models.CharField(max_length=20, choices=PAY_CHOICES, default='question', verbose_name='Статус оплаты')
    payment_type = models.CharField(max_length=32, blank=True, null=True, choices=PAYMENT_TYPE_CHOICES,
                                    verbose_name='Способ оплаты')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='buy', verbose_name='Тип обращения')
    date = models.DateField(blank=True, null=True, verbose_name='Дата для связи с клиентов')
    time = models.DateField(auto_now_add=True, verbose_name='Время заказа')
    close_time = models.DateField(blank=True, null=True, verbose_name='Время завершения заказа')
    have_new_message = models.BooleanField(default=False, verbose_name='Есть ли новое сообщение?')
    last_message_time = models.DateTimeField(blank=True, null=True, verbose_name='Время последнего сообщения')

    def date_str(self):
        month = self.date.month
        day = self.date.day
        if month < 10:
            month = f'0{month}'
        if day < 10:
            day = f'0{day}'
        date = f'{self.date.year}-{month}-{day}'
        return date
    def get_cardholder(self):
        if self.card_holder_id:
            return int(self.card_holder_id)
        return None


class Text(models.Model):
    SENDER_CHOISE = (
        ('manager', 'Менеджер'),
        ('client', 'Клиент')
    )
    order = models.ForeignKey('Order', related_name='texts', on_delete=models.CASCADE, verbose_name='Заказ')
    text = models.TextField(blank=True, null=True, verbose_name='Текст сообщения')
    file_id = models.CharField(blank=True, max_length=256, null=True,
                               verbose_name='Аватарка пользователя 1')
    is_text = models.BooleanField(default=True, verbose_name='Является ли сообщение текстом')
    is_photo = models.BooleanField(default=False, verbose_name='Является ли сообщение фото')
    is_pdf = models.BooleanField(default=False, verbose_name='Является ли сообщение pdf')
    base64_file = models.TextField(blank=True, null=True, verbose_name='Файл в формате base64')
    time = models.DateTimeField(auto_now_add=True, verbose_name='Дата сообщения')
    sender = models.CharField(max_length=10, choices=SENDER_CHOISE, verbose_name='Отправитель')

    def get_data(self):
        if not self.base64_file:
            try:
                file_id = self.file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                encoded_string = base64.b64encode(downloaded_file).decode('utf-8')
                self.base64_file = encoded_string
                self.save(update_fields=['base64_file'])
            except Exception:
                return None
        return self.base64_file


class ClientActions(models.Model):
    client = models.ForeignKey('Client', related_name='actions', on_delete=models.CASCADE, verbose_name='Клиент')
    action = models.CharField(max_length=256, verbose_name='Действие')


class ManagerActions(models.Model):
    manager = models.ForeignKey('Manager', related_name='actions', on_delete=models.CASCADE, verbose_name='Менеджер')
    action = models.CharField(max_length=256, verbose_name='Действие')
    time = models.DateTimeField(auto_now_add=True)


class Mailing(models.Model):
    date = models.DateField(auto_now_add=True)
    text = models.TextField(verbose_name='Текст рассылки')
    send_users = models.IntegerField(default=0, verbose_name='Какому кол-ву произошла отправка')
    buy_users = models.IntegerField(default=0,
                                    verbose_name='Сколько пользователей в течении 72 совершили хотя бы 1 покупку')
    buy_summ = models.DecimalField(max_digits=10, blank=True, null=True, decimal_places=2,
                                   verbose_name='Сумма покупок с учетом доли ДК, МОПА и реферальной доли')


class BalanceHistory(models.Model):
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма балансов пользователей')
    date = models.DateField(auto_now_add=True)


class Active_users(models.Model):
    buy_users_count = models.ManyToManyField('Client', blank=True,
                                             verbose_name='Кол-во пользователей, которые купили что-либо',
                                             related_name='bought_active_users')
    user_action_count = models.ManyToManyField('Client', blank=True,
                                               verbose_name='Кол-во пользователей, которые совершили хотя бы одно действие',
                                               related_name='action_active_users')
    date = models.DateField(auto_now_add=True)


class BotText(models.Model):
    name = models.CharField(max_length=128)
    text = models.TextField(default='Пустое текстовое поле')
