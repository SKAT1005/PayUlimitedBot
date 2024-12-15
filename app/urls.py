from django.urls import path

from .views import login_view, MainView, ProfileView, MailingView, change_status

urlpatterns = [
    path("", login_view, name="login"),
    path('main', MainView.as_view(), name="main"),
    path('profile', ProfileView.as_view(), name="profile"),
    path('mailing', MailingView.as_view(), name="mailing"),
    path('change_status', change_status, name="change_status"),
]
