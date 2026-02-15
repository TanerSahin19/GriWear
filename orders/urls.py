# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ✅ Checkout (GET: sayfa göster / POST: siparişi yaz)
    path("checkout/", views.checkout, name="checkout"),

    # ✅ Başarı sayfası
    path("success/<int:order_id>/", views.success, name="success"),

    # ✅ Siparişlerim
    path("my-orders/", views.my_orders, name="my_orders"),

    # ✅ Sipariş detay
    path("my-orders/<int:order_id>/", views.order_detail, name="order_detail"),
    
    
    path("my-orders/<int:order_id>/cancel/", views.cancel_order, name="cancel_order"),


]
