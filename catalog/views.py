from django.shortcuts import render, get_object_or_404
from urllib3 import request
from .models import Category, Product
from django.db.models import Q

def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")
    return render(request, "catalog/list.html", {"products": products})


def new_arrivals_view(request):
    products = Product.objects.filter(is_active=True, is_new=True).select_related("category")
    return render(request, "catalog/new_arrivals.html", {"products": products})


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category).select_related("category")
    return render(
        request,
        "catalog/category.html",
        {"category": category, "products": products},
    )
def search_view(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.filter(is_active=True)
    if q:
        products = products.filter(name__icontains=q)

    return render(request, "catalog/search.html", {"products": products, "q": q})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/detail.html", {"product": product})



def search(request):
    q = (request.GET.get("q") or "").strip()

    products = Product.objects.none()

    if q:
        products = (
            Product.objects
            .filter(is_active=True)
            .filter(Q(name__icontains=q) | Q(description__icontains=q))
            .order_by("-created_at")  # en yeni önce (modelinle uyumlu)
        )

    context = {
        "q": q,
        "products": products,
        "count": products.count() if q else 0,
    }
     
    return render(request, "catalog/search.html", context)