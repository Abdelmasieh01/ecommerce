from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'username',)

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class ItemDetailSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Item
        fields = ('id', 'title', 'description', 'price', 'seller', 'image')

class ItemListSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.username', read_only=True)
    class Meta:
        model = Item
        fields = ('id', 'title', 'price', 'seller', 'image')

class OrderSerializer(serializers.ModelSerializer):
    item = ItemListSerializer()
    user = UserSerializer()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ('id','item', 'user', 'item_count', 'total_price', 'status', 'status_display')