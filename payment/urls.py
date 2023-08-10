from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('choose-payment/<int:id>/', views.choose_payment, name='choose-payment'),
    path('pay-by-card/<int:id>/', views.initiate_payment_card, name='initiate-payment-card'),
    path('pay-by-mob/<int:id>/', views.initiate_payment_mob, name='initiate-payment-mob'),
    path('error/', views.payment_error, name='error'),
]   