from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'main'

router = DefaultRouter()
router.register(r'items', views.ItemViewSet, basename='item')

urlpatterns = [
    path('users/<int:id>/', views.UserDetailAPIView.as_view(), name='user'),
    path('', include(router.urls)),
    path('orders/', views.OrderListAPIView.as_view(), name='my-orders')
]