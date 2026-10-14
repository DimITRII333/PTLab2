from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('order/', views.PurchaseCreate.as_view(), name='order'),
    path('buy/<int:product_id>/', views.PurchaseCreate.as_view(), name='buy'),
]
