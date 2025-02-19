from django.urls import path

from .views import login_view, MainView, ProfileView, MailingView, change_status, get_messages, StatisticsView, Logout_View, check_new_order

urlpatterns = [
    path("", login_view, name="login"),
    path('logout', Logout_View.as_view(), name='logout'),
    path('main', MainView.as_view(), name="main"),
    path('profile', ProfileView.as_view(), name="profile"),
    path('mailing', MailingView.as_view(), name="mailing"),
    path('change_status', change_status, name="change_status"),
    path('check_new_messages', get_messages, name='get_messages'),
    path('check_new_order', check_new_order, name='check_new_order'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
]
