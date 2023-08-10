from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import requests
from main.models import Order, Item

# Create your views here.
@login_required()
def choose_payment(request, id):
    # if request.method == 'POST':
    #     method = request.POST.get('type', 'card')
    #     if method == 'card':
    #         return redirect('payment:initiate-payment-card', id=id)
    #     elif method == 'phone':
    #         return redirect('payment:initiate-payment-mob', id=id)
    return render(request, 'payment/choose.html', {'id': id})

@login_required()
def initiate_payment_card(request, id):
    '''
    Gives the user an iframe to pay for the order
    '''
    CARD_INTEGRATION_ID = 4075697
    order = get_object_or_404(Order, pk=id)
    if order.user != request.user:
        return redirect('payment:error')
    payment_key = request_payment_key(order, CARD_INTEGRATION_ID)
    card_iframe_url = f'https://accept.paymob.com/api/acceptance/iframes/778662?payment_token={payment_key}'
    return render(request, 'payment/payment-card.html', {'card_iframe_url': card_iframe_url})

@login_required()
def initiate_payment_mob(request, id):
    '''
    Redirects the user to the url to pay from their mobile wallet
    '''
    if request.method == 'POST':
        WALLET_INTEGRATION_ID = 4082739
        order = get_object_or_404(Order, pk=id)
        if order.user != request.user:
            return redirect('payment:error')
        phone = request.POST.get('phone')
        token = request_payment_key(order, WALLET_INTEGRATION_ID)
    
        json_body = {
            "source": {
                "identifier": phone,
                "subtype": "WALLET"
            },
            "payment_token": token
        }
        response = requests.post('https://accept.paymob.com/api/acceptance/payments/pay', json=json_body)

        if response.status_code == 201:
            content = json.loads(response.content.decode())
            return redirect(content.get('redirect_url', 'payment:error'))
        else:
            return redirect('payment:error')
    return render(request, 'payment/payment-mobile.html', ) 

def payment_error(request):
    return render(request, 'payment/payment-error.html', )



def get_token() -> str:
    '''
    Makes a request to Paymob server to get the token for the merchant account
    '''
    json_body = {
        'api_key': settings.PAYMOB_API_KEY
    }
    response = requests.post(
        'https://accept.paymob.com/api/auth/tokens', json=json_body)
    if response.status_code == 201:
        content = json.loads(response.content.decode())
        return content['token']
    else:
        return redirect('payment:error')
    # print(content['token'])


def register_order(order: Order):
    '''
    Makes a post request to register the order to Paymob server and returns the order_id
    '''
    token = get_token()
    item = order.item
    json_body = {
        'auth_token': token,
        'delivery_needed': 'false',
        'amount_cents': f'{int(order.total_price * 100)}',
        'currency': 'EGP',
        'items': [
            {
                'name': item.title,
                'amount_cents': f'{int(item.price * 100)}',
                'description': item.description,
                'quantity': order.item_count
            }
        ]
    }
    response = requests.post(
        'https://accept.paymob.com/api/ecommerce/orders', json=json_body)
    if response.status_code == 201:
        content = json.loads(response.content.decode())
        return token, content['id']
    else:
        return redirect('payment:error')


def request_payment_key(order: Order, integration_id: int):
    '''
    Makes a request to have the final token required for payment
    '''
    token, order_id = register_order(order)
    json_body = {
        'auth_token': token,
        'amount_cents': f'{int(order.total_price * 100)}',
        'expiration': 3600,
        'order_id': order_id,
        "billing_data": {
            "apartment": "NA",
            "email": f'{order.user.email}',
            "floor": "NA",
            "first_name": f'{order.user.first_name}',
            "street": "NA",
            "building": "NA",
            "phone_number": "+201558345185",
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "NA",
            "country": "NA",
            "last_name": f'{order.user.last_name}',
            "state": "NA"
        },
        'currency': 'EGP',
        'integration_id': integration_id,
        "lock_order_when_paid": "false"  # false for now
    }

    response = requests.post(
        'https://accept.paymob.com/api/acceptance/payment_keys', json=json_body)
    if response.status_code == 201:    
        content = json.loads(response.content.decode())
        return content['token']
    else:
        return redirect('payment:error')
