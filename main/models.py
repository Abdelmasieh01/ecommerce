from typing import Any
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

# Create your models here.
class Item(models.Model):
    title = models.CharField(max_length=150, verbose_name='Title')
    description = models.TextField(verbose_name='Item Description')
    price = models.DecimalField(verbose_name='Item Price', max_digits=10, decimal_places=2)
    seller = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Merchant', related_name='items', )
    image = models.ImageField(verbose_name='Item Image', upload_to='items/images/')

    def __str__(self):
        return f'Item: {self.title} | Sold By: {self.seller.username}'

class Order(models.Model):
    UNPAID = 0
    PAID = 1
    FAILED = 2
    CHOICES = [
        (UNPAID, 'Unpaid'),
        (PAID, 'Paid'),
        (FAILED, 'Failed'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    item_count = models.PositiveSmallIntegerField()
    status = models.PositiveSmallIntegerField(choices=CHOICES, default=0)
    
    @property
    def total_price(self):
        return self.item.price * self.item_count
    
    def __str__(self):
        return f'Item: {self.item.title} | Count: {self.item_count} | By: {self.user.get_username()}'
    
    