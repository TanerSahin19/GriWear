from django.shortcuts import redirect, render, get_object_or_404
from catalog.models import Product
from django.contrib import messages


CART_SESSION_KEY = "cart"


def _get_cart(session):
    cart = session.get(CART_SESSION_KEY)
    if cart is None:
        cart = {}
        session[CART_SESSION_KEY] = cart
    return cart


def cart_remove(request, product_id):
    cart = _get_cart(request.session)
    pid = str(product_id)

    if pid in cart:
        del cart[pid]
        request.session.modified = True

    return redirect("cart:detail")

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # 🔒 1) Stok 0 kontrolü
    if product.stock <= 0:
        messages.error(request, "Bu ürün tükendi.")
        return redirect("catalog:product_detail", slug=product.slug)

    cart = _get_cart(request.session)
    pid = str(product.id)

    current_qty = cart.get(pid, {}).get("qty", 0)

    # 🔒 2) Stok limit kontrolü
    if current_qty + 1 > product.stock:
        messages.warning(request, "Stok limiti aşılamaz. Daha fazla ekleyemezsin.")
        return redirect("cart:detail")

    # 🔒 3) Sepete ekle
    if pid in cart:
        cart[pid]["qty"] += 1
    else:
        cart[pid] = {"qty": 1}

    request.session.modified = True
    return redirect("cart:detail")

    product = get_object_or_404(Product, id=product_id, is_active=True)

    cart = _get_cart(request.session)
    pid = str(product.id)

    # ✅ 1) Stok 0 ise ekleme yok
    if product.stock <= 0:
        return redirect("cart:detail")

    current_qty = cart.get(pid, {}).get("qty", 0)

    # ✅ 2) Stok sınırı: mevcut + 1 > stock ise arttırma yok
    if current_qty + 1 > product.stock:
        return redirect("cart:detail")

    # ✅ Ekleme
    if pid in cart:
        cart[pid]["qty"] += 1
    else:
        cart[pid] = {"qty": 1}

    request.session.modified = True
    return redirect("cart:detail")

def cart_detail(request):
    cart = _get_cart(request.session)

    # ürünleri çek
    product_ids = [int(pid) for pid in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=product_ids, is_active=True)

    items = []
    total = 0

    for p in products:
        qty = cart.get(str(p.id), {}).get("qty", 0)
        subtotal = qty * float(p.price)
        total += subtotal
        items.append({
            "product": p,
            "qty": qty,
            "subtotal": subtotal,
        })

    return render(request, "cart/detail.html", {"items": items, "total": total})
