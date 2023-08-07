from rest_framework import generics
from rest_framework import viewsets
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from .serializers import *
    
class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().prefetch_related('seller')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ItemListSerializer
        
        elif self.action == 'retrieve':
            return ItemDetailSerializer
        
        else:
            return ItemSerializer
    
    def perform_create(self, serializer):
        serializer.seller = self.request.user
        return super().perform_create(serializer)
    
class OrderListAPIView(LoginRequiredMixin, generics.ListAPIView):
    serializer_class = OrderSerializer
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    
