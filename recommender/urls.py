from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('chat/responder/', views.chat_responder, name='chat_responder'),
    path('chat/<int:conv_id>/', views.ver_conversacion, name='ver_conversacion'),
    path('registro/', views.registro, name='registro'),
] 