from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import requests
import hmac
import hashlib
from flatdict import FlatDict
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
        response = requests.post(
            'https://accept.paymob.com/api/acceptance/payments/pay', json=json_body)

        if response.status_code == 200:
            content = json.loads(response.content.decode())
            try:
                return redirect(content.get('redirect_url'))
            except:
                return redirect('payment:error')
        else:
            return redirect('payment:error')
    return render(request, 'payment/payment-mob.html', )


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
        order.accept_id = content['id']
        order.save()
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


class OrderStatus(APIView):
    '''
    Webhook to check and edit order status
    '''
    permission_classes = [AllowAny]

    def verify_signature(self, received_signature: str, payload):
        HMAC_KEY = settings.HMAC_KEY
        HMAC_STRING_KEYS = [
            "amount_cents", "created_at", "currency", "error_occured",
            "has_parent_transaction", "obj.id", "integration_id", "is_3d_secure",
            "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
            "is_voided", "order.id", "owner", "pending", "source_data.pan",
            "source_data.sub_type", "source_data.type", "success"
        ]
        flat_payload = dict(FlatDict(payload['obj'], delimiter='.'))
        hmac_string = ''.join(str(flat_payload[key]) for key in HMAC_STRING_KEYS).replace('False', 'false').replace('True', 'true')
        calculated_signature = hmac.new(
            HMAC_KEY.encode('utf-8'), 
            hmac_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        if hmac.compare_digest(calculated_signature, received_signature):
            return True
        return False

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        payload = request.data
        received_signature = request.query_params.get('hmac')
        if not received_signature:
            return Response(
                {'detail': 'Permission Denied.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        is_valid = self.verify_signature(received_signature, payload)
        if not is_valid:
            return Response(
                {'detail': 'Permission Denied.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
        order_accept_id = payload.get('obj', {}).get('order', {}).get('id')
        order_success = payload.get('obj', {}).get('success')
        order = get_object_or_404(Order, accept_id=order_accept_id)
        if order_success:
            order.status = Order.PAID
            order.save()

        return Response(
            {'detail': 'Payment done successfully.'},
            status=status.HTTP_202_ACCEPTED
        )