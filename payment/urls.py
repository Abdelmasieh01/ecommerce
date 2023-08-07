from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('initiate/<int:id>/', views.initiate_payment, name='initiate-payment'),
    path('initiate/pay-by-mob/', views.pay_by_mob, name='pay-by-mob'),
]   