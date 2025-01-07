import re
from datetime import datetime, timedelta, date

from django.db.models import Sum, ExpressionWrapper, F, FloatField, Count, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.chart import PieChart, Reference, LineChart
from openpyxl.chart.axis import NumericAxis
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule
from .models import *

wb = Workbook()


def transform_data_heart_map(data_dict: dict) -> list:
    # Функция для извлечения числового значения из ключа месяца
    def extract_month_number(month_key):
        match = re.match(r'(\d+)', str(month_key))
        if match:
            return int(match.group(1))
        return float('inf')  # Если не удалось, ставим бесконечность для сортировки в конец

    # Функция для извлечения числового значения из ключа покупки
    def extract_purchase_number(purchase_key):
        match = re.match(r'(\d+)', purchase_key)
        if match:
            return int(match.group(1))
        return -1  # Если не удалось, ставим -1 для сортировки в начало

    # 1. Извлекаем и сортируем месяцы по возрастанию их числового значения
    months = sorted(data_dict.keys(), key=extract_month_number)

    # 2. Извлекаем все уникальные типы покупок
    purchase_set = set()
    for month_data in data_dict.values():
        purchase_set.update(month_data.keys())

    # 3. Сортируем покупки по убыванию их числового значения
    purchases = sorted(purchase_set, key=extract_purchase_number, reverse=True)

    # 4. Формируем строки с данными
    rows = []
    for purchase in purchases:
        row = [purchase]
        for month in months:
            value = data_dict.get(month, {}).get(purchase, 0)
            row.append(value)
        rows.append(row)

    # 5. Формируем заголовок
    header = ['Кол-во покупок/Месяцев с последней покупки'] + months

    # 6. Добавляем заголовок в конец списка
    rows.append(header)

    return rows


def heart_map_data():
    users = Client.objects.all()
    data_dict = {}
    for user in users:
        orders = user.orders_for_user.filter(type__in=['buy', 'not_find_product'], pay_status='complite')
        orders_count = orders.count()
        orders_count_str = f'{orders.count()} Покупка'
        if orders_count > 0:
            last_order_time = timezone.now() - timedelta(days=10)
            n = timezone.now() - last_order_time
            month = 0
            try:
                month += n.year * 12
            except Exception:
                pass
            try:
                month += n.month
            except Exception:
                pass
            month_str = f'{month} Месяц'
            if month_str in data_dict:
                if orders_count_str in data_dict[month]:
                    data_dict[month][orders_count_str] += 1
                else:
                    data_dict[month][orders_count_str] = 1
            else:
                data_dict[month] = {orders_count_str: 1}
    return transform_data_heart_map(data_dict)


def heart_map(wb):
    ws = wb.active
    ws.title = 'Тепловая карта'

    # Данные для тепловой карты
    data = heart_map_data()

    for row in data:
        ws.append(row)

    # Создаем правило условного форматирования ColorScale
    color_scale_rule = ColorScaleRule(start_type='min',
                                      start_color='00CC00',
                                      mid_type='percentile',
                                      mid_value=25,
                                      mid_color='FFFF33',
                                      end_type='max',
                                      end_color='FFFF0000')

    # Применяем правило ко всему диапазону данных
    ws.conditional_formatting.add('B1:AA1000', color_scale_rule)


def revenue_structure_data(startdate, enddate):
    orders = Order.objects.filter(time__range=(startdate, enddate), type__in=['buy', 'not_find_product'],
                                  pay_status='complite')
    total_purchases = orders

    # 2. Вычисляем общую выручку как сумму (total_product_price - product_price) для всех заказов
    #    Используем ExpressionWrapper для создания выражения разницы
    total_revenue = total_purchases.aggregate(
        total_revenue=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('total_product_price') - F('product_price'),
                    output_field=IntegerField()
                )
            ),
            0
        )
    )['total_revenue']

    # 3. Группируем заказы по сервису и подсчитываем количество заказов и суммарную выручку для каждого сервиса
    services = Order.objects.values('name').annotate(
        purchases=Count('id'),
        revenue=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('total_product_price') - F('product_price'),
                    output_field=IntegerField()
                )
            ),
            0
        )
    ).order_by('name')  # Можно изменить порядок сортировки по необходимости

    # 4. Формируем итоговый список с процентами
    data = []
    for service in services:
        service_name = service['name'] or 'Неизвестный сервис'  # Обработка возможных NULL значений
        purchases = service['purchases']
        revenue = service['revenue']

        # Вычисляем проценты, избегая деления на ноль
        percentage_purchases = (purchases / total_purchases.count() * 100) if total_purchases.count() > 0 else 0
        percentage_revenue = (revenue / total_revenue * 100) if total_revenue > 0 else 0

        # Округляем проценты до двух знаков после запятой для наглядности
        percentage_purchases = round(percentage_purchases, 2)
        percentage_revenue = round(percentage_revenue, 2)

        data.append([service_name, percentage_purchases, percentage_revenue])

    return data


def revenue_structure(wb, startdate, enddate):
    ws = wb.create_sheet("Структура выручки")

    data = [
               ["", "% от выручки", '% от продаж'],
           ] + revenue_structure_data(startdate, enddate)

    for row in data:
        ws.append(row)

    pie1 = PieChart()
    pie2 = PieChart()
    labels = Reference(ws, min_col=1, min_row=2, max_row=len(data))
    data_values1 = Reference(ws, min_col=2, min_row=2, max_row=len(data))
    data_values2 = Reference(ws, min_col=3, min_row=2, max_row=len(data))

    pie1.add_data(data_values1)
    pie2.add_data(data_values2)

    pie1.set_categories(labels)
    pie2.set_categories(labels)

    pie1.title = "% От выручки"

    pie1.dataLabels = DataLabelList()
    pie1.dataLabels.showPercent = True  # Показывать проценты
    pie1.dataLabels.showVal = False  # Отключить абсолютные значения
    pie1.dataLabels.showCatName = False  # Отключить подписи категорий
    pie1.dataLabels.showSerName = False  # Отключить подпись "Ряд 1"

    pie2.title = "% От продаж"
    pie2.dataLabels = DataLabelList()
    pie2.dataLabels.showPercent = True
    pie2.dataLabels.showVal = False
    pie2.dataLabels.showCatName = False
    pie2.dataLabels.showSerName = False

    ws.add_chart(pie1, "F1")
    ws.add_chart(pie2, "P1")


def iterate_days(start_date, end_date):
    start_date = datetime(year=int(start_date.split('-')[0]), month=int(start_date.split('-')[1]),
                          day=int(start_date.split('-')[2]))
    end_date = datetime(year=int(end_date.split('-')[0]), month=int(end_date.split('-')[1]),
                        day=int(end_date.split('-')[2]))
    delta = end_date - start_date  # Разница между датами

    for i in range(delta.days + 1):
        yield start_date + timedelta(days=i)


def statistics_for_each_service_data(startdate, enddate):
    dates = [i for i in iterate_days(startdate, enddate)]
    data1 = [
        [None, ] + dates,
    ]
    data2 = [
        [None] + dates,
    ]
    for product in Products.objects.all():
        prod1 = [product.name]
        prod2 = [product.name]
        for date in dates:
            orders = Order.objects.filter(name=product.name, time=date.strftime("%Y-%m-%d"),
                                          type__in=['buy', 'not_find_product'],
                                          pay_status='complite')
            if orders:
                total_purchases = orders.count()
                total_revenue = orders.aggregate(
                    total_revenue=Sum(F('total_product_price') - F('product_price'))
                )['total_revenue']

                prod1.append(total_purchases)
                prod2.append(total_revenue or 0)
            else:
                prod1.append(0)
                prod2.append(0)
        data1.append(prod1)
        data2.append(prod2)
    return data1, data2


def statistics_for_each_service(wb, startdate, enddate):
    ws = wb.create_sheet("Статистика для каждого сервиса")
    data1, data2 = statistics_for_each_service_data(startdate, enddate)

    # Запишем данные построчно на лист
    for row in data1:
        ws.append(row)

    for row in data2:
        ws.append(row)

    # Создаём линейный график
    chart1 = LineChart()
    chart1.title = "Кол-во сделок"

    chart2 = LineChart()
    chart2.title = "Прибыль"

    cats1 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=1, max_row=1)
    cats2 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=len(data1) + 1, max_row=len(data1) + 1)
    chart1.set_categories(cats1)
    chart2.set_categories(cats2)

    data_ref1 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=2, max_row=len(data1))
    data_ref2 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=2 + len(data1), max_row=len(data1) * 2)
    chart1.add_data(data_ref1, from_rows=True, titles_from_data=True)
    chart2.add_data(data_ref2, from_rows=True, titles_from_data=True)

    chart1.y_axis = NumericAxis()
    chart1.y_axis.majorTickMark = "cross"
    chart1.y_axis.delete = False

    chart2.y_axis = NumericAxis()
    chart2.y_axis.majorTickMark = "cross"
    chart2.y_axis.delete = False

    ws.add_chart(chart1, "I1")
    ws.add_chart(chart2, "I16")


def deal_stats_date(startdate, enddate):
    dates = [i for i in iterate_days(startdate, enddate)]
    data_1_new = [[], [], []]
    data_2_new = [[], [], []]
    for date in dates:
        orders = Order.objects.filter(time=date.strftime("%Y-%m-%d"), type__in=['buy', 'not_find_product'],
                                      pay_status='complite')
        total_purchases = orders.count()
        total_purchases_new_user = orders.filter(is_first_buy=True).count()
        total_purchases_old_user = orders.filter(is_first_buy=False).count()

        total_revenue = orders.aggregate(
            total_revenue=Sum(F('total_product_price') - F('product_price'))
        )['total_revenue']
        total_revenue_new_user = \
            orders.filter(is_first_buy=True).aggregate(
                Sum__total_product_price__sub=Sum(F('total_product_price') - F('product_price'))
            )[
                'Sum__total_product_price__sub']
        total_revenue_old_user = \
            orders.filter(is_first_buy=False).aggregate(
                Sum__total_product_price__sub=Sum(F('total_product_price') - F('product_price'))
            )[
                'Sum__total_product_price__sub']

        data_1_new[0].append(total_purchases)
        data_1_new[1].append(total_purchases_new_user)
        data_1_new[2].append(total_purchases_old_user)

        data_1_new[0].append(total_revenue)
        data_1_new[1].append(total_revenue_new_user)
        data_1_new[2].append(total_revenue_old_user)

    return dates, data_1_new, data_2_new


def deal_stats(wb, startdate, enddate):
    ws = wb.create_sheet("Статистика по сделкам")
    dates, data_1_new, data_2_new = deal_stats_date(startdate, enddate)
    data1 = [
        [None] + dates,
        ["Всего сделок"] + data_1_new[0],
        ["Сделки новых пользователей"] + data_1_new[1],
        ["Сделки старых пользователей"] + data_1_new[2],
    ]
    data2 = [
        [None] + dates,
        ["Общая выручка"] + data_2_new[0],
        ["Выручка от новых пользователей"] + data_2_new[1],
        ["Выручка от старых пользователей"] + data_2_new[2],
    ]

    # Запишем данные построчно на лист
    for row in data1:
        ws.append(row)

    for row in data2:
        ws.append(row)

    # Создаём линейный график
    chart1 = LineChart()
    chart1.title = "Кол-во сделок"

    chart2 = LineChart()
    chart2.title = "Прибыль"

    cats1 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=1, max_row=1)
    cats2 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=5, max_row=5)

    chart1.set_categories(cats1)
    chart2.set_categories(cats2)

    data_ref1 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=2, max_row=4)
    data_ref2 = Reference(ws, min_col=1, max_col=len(data1[0]), min_row=6, max_row=8)
    chart1.add_data(data_ref1, from_rows=True, titles_from_data=True)
    chart2.add_data(data_ref2, from_rows=True, titles_from_data=True)

    chart1.y_axis = NumericAxis()
    chart1.y_axis.majorTickMark = "cross"
    chart1.y_axis.delete = False

    chart2.y_axis = NumericAxis()
    chart2.y_axis.majorTickMark = "cross"
    chart2.y_axis.delete = False

    ws.add_chart(chart1, "I1")
    ws.add_chart(chart2, "I16")


def mailing_stats_data(startdate, enddate):
    data = []
    for mail in Mailing.objects.filter(date__range=[startdate, enddate]):
        data.append([mail.date, mail.text, mail.send_users, mail.buy_users, mail.buy_users])
    return data


def mailing_stats(wb, startdate, enddate):
    ws = wb.create_sheet("Статистика рассылки")
    data = [
               ["Дата рассылки", "Текст рассылки", "Кол-во получивших", "Купили за 3 дня", "Сумма покупок"]
           ] + mailing_stats_data(startdate, enddate)
    for row in data:
        ws.append(row)


def conversion_data(startdate, enddate):
    startdate = date(year=int(startdate.split('-')[0]), month=int(startdate.split('-')[1]),
                          day=int(startdate.split('-')[2]))
    enddate = date(year=int(enddate.split('-')[0]), month=int(enddate.split('-')[1]),
                        day=int(enddate.split('-')[2]))
    first = [0, 0, 0]
    second = [0, 0, 0]
    for user in Client.objects.filter(join_time__range=[startdate, enddate]):
        if user.stay_new and startdate <= user.stay_new <= enddate:
            first[0] += 1
            if user.stay_old and startdate <= user.stay_old <= enddate:
                first[1] += 1
        elif startdate <= user.join_time <= enddate:
            second[0] += 1
            if user.stay_new and startdate <= user.stay_new <= enddate:
                second[1] += 1
    try:
        first_persent = int(first[1] / first[0] * 100)
    except Exception:
        first_persent = 0
    try:
        second_persent = int(second[1] / second[0] * 100)
    except Exception:
        second_persent = 0
    first[2] = f'{first_persent}%'
    second[2] = f'{second_persent}%'

    return first, second


def conversion(wb, startdate, enddate):
    ws = wb.create_sheet("Конверсия")
    first, second = conversion_data(startdate, enddate)
    data = [
        ['Новые клиенты', 'Стали старыми', 'Процент'],
        first,
        [None, None, None],
        ['Кол-во вступивших в бота', 'Кол-во новых клиентов', 'Процент'],
        second
    ]
    for row in data:
        ws.append(row)


def active_users_data(startdate, enddate):
    dates = [i for i in iterate_days(startdate, enddate)]
    first = []
    second = []
    for active in Active_users.objects.filter(date__range=[startdate, enddate]):
        first.append(active.buy_users_count.count())
        second.append(active.user_action_count.count())
    return dates, first, second


def active_users(wb, startdate, enddate):
    ws = wb.create_sheet("Активные пользователи")
    dates, first, second = active_users_data(startdate, enddate)
    data = [
        [None] + dates,
        ["Совершили покупку"] + first,
        ["Нажали кнопку"] + second,
    ]
    for row in data:
        ws.append(row)
    chart = LineChart()
    chart.title = "Активность пользователей"

    cats = Reference(ws, min_col=1, max_col=len(data[0]), min_row=1, max_row=1)

    chart.set_categories(cats)

    data_ref = Reference(ws, min_col=1, max_col=len(data[0]), min_row=2, max_row=len(data))
    chart.add_data(data_ref, from_rows=True, titles_from_data=True)

    chart.y_axis = NumericAxis()
    chart.y_axis.majorTickMark = "cross"
    chart.y_axis.delete = False

    ws.add_chart(chart, "A5")


def balance_stat_data(startdate, enddate):
    dates = [i for i in iterate_days(startdate, enddate)]
    balance_summ = []
    for balance in BalanceHistory.objects.filter(date__range=[startdate, enddate]):
        balance_summ.append(balance.total_balance)
    return dates, balance_summ


def balance_stat(wb, startdate, enddate):
    ws = wb.create_sheet("Статистика балансов")
    dates, balance_summ = balance_stat_data(startdate, enddate)
    data = [
        [None] + dates,
        ["Сумма балансов"] + balance_summ,
    ]
    for row in data:
        ws.append(row)

    chart = LineChart()
    chart.title = "Сумма балансов пользоватлей"

    cats = Reference(ws, min_col=1, max_col=len(data[0]), min_row=1, max_row=1)

    chart.set_categories(cats)

    data_ref = Reference(ws, min_col=1, max_col=len(data[0]), min_row=2, max_row=len(data))
    chart.add_data(data_ref, from_rows=True, titles_from_data=True)

    chart.y_axis = NumericAxis()
    chart.y_axis.majorTickMark = "cross"
    chart.y_axis.delete = False

    ws.add_chart(chart, "A5")


def expenses_stats(wb, startdate, enddate):
    ws = wb.create_sheet("Статистика расходов")
    data = [
        [None, "2024-12-23", "2024-12-25", "2024-12-27", "2024-12-29", "2024-12-31", "2025-01-02"],
        ["Сумма трат:", 500, 300, 700, 700, 800, 900],
    ]
    for row in data:
        ws.append(row)

    chart = LineChart()
    chart.title = "Статистика трат"

    cats = Reference(ws, min_col=1, max_col=len(data[0]), min_row=1, max_row=1)

    chart.set_categories(cats)

    data_ref = Reference(ws, min_col=1, max_col=len(data[0]), min_row=2, max_row=len(data))
    chart.add_data(data_ref, from_rows=True, titles_from_data=True)

    chart.y_axis = NumericAxis()
    chart.y_axis.majorTickMark = "cross"
    chart.y_axis.delete = False

    ws.add_chart(chart, "A5")
