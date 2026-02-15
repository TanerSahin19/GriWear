from django.urls import path
from . import views 

app_name = "catalog"

urlpatterns = [
    path("urunler/", views.product_list, name="product_list"),
    path("kategori/<slug:slug>/", views.category_view, name="category_products"),
    path("urun/<slug:slug>/", views.product_detail, name="product_detail"),
    path("yeni-gelenler/", views.new_arrivals_view, name="new_arrivals"),
    path("search/", views.search, name="search"),

]
