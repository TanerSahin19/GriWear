# ============================================================
# orders/views.py  —  GRİWEAR (KİLİTLİ BACKEND)
# Amaç: Checkout’ta 2. stok kapısı (transaction + select_for_update)
# Not: Bu dosyada checkout TEK KEZ var. Kopya view yok.
# ============================================================

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from catalog.models import Product
from .forms import CheckoutForm
from .models import Order, OrderItem
from django.views.decorators.http import require_POST

# ============================================================
# 1) SESSION CART AYARLARI — NEDEN?
# ============================================================
# Sepet DB’ye yazılmadan önce geçici bir yapıdır.
# Kullanıcı ekler/çıkarır/adet değiştirir. Bu yüzden session’da tutulur.
CART_SESSION_KEY = "cart"


def _get_cart(session):
    # ------------------------------------------------------------
    # Bu fonksiyon ne yapar?
    # - session içindeki 'cart' sözlüğünü getirir
    # - yoksa boş {} döner
    # ------------------------------------------------------------
    return session.get(CART_SESSION_KEY, {})


def _clear_cart(session):
    # ------------------------------------------------------------
    # Bu fonksiyon ne yapar?
    # - Sipariş tamamlandıktan sonra sepeti session’dan siler
    # - session.modified = True ile değişikliği kaydettirir
    # ------------------------------------------------------------
    if CART_SESSION_KEY in session:
        del session[CART_SESSION_KEY]
        session.modified = True


# ============================================================
# 2) CHECKOUT — NEDEN LOGIN ŞART?
# ============================================================
# login_required ne yapar?
# - giriş yoksa checkout’a sokmaz
# - sipariş kullanıcıya bağlanır → "Siparişlerim" çalışır
# - güvenlik: herkes herkesin siparişini göremez
@login_required
def checkout(request):
    # ------------------------------------------------------------
    # 2A) SEPETİ OKU
    # ------------------------------------------------------------
    cart = _get_cart(request.session)

    # ------------------------------------------------------------
    # 2B) 1. KONTROL: SEPET BOŞSA CHECKOUT YOK
    # ------------------------------------------------------------
    if not cart:
        messages.warning(request, "Sepetiniz boş. Checkout yapılamaz.")
        return redirect("cart:detail")

    # ------------------------------------------------------------
    # 2C) SEPETTEKİ ÜRÜNLERİ DB’DEN ÇEK
    # ------------------------------------------------------------
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids, is_active=True)

    # ------------------------------------------------------------
    # 2D) SAYFADA GÖSTERMEK İÇİN ITEMS + TOTAL HESAPLA
    # items: template’e gidecek satırlar
    # total: sipariş toplamı
    # line_total: her ürün fiyat * adet
    # ------------------------------------------------------------
    items = []
    total = 0

    for p in products:
        pid = str(p.id)
        qty = int(cart.get(pid, {}).get("qty", 0))

        if qty <= 0:
            continue

        line_total = p.price * qty
        total += line_total

        items.append({
            "product": p,
            "quantity": qty,
            "line_total": line_total,
        })

    # ------------------------------------------------------------
    # 2E) 2. KONTROL: ITEMS BOŞSA (GEÇERLİ ÜRÜN YOKSA)
    # ------------------------------------------------------------
    if not items:
        messages.warning(request, "Sepetiniz boş.")
        return redirect("cart:detail")

    # ============================================================
    # 3) POST / GET AYRIMI
    # ============================================================
    # GET: checkout sayfası + boş form
    # POST: form gönderildi → sipariş yazma başlar
    if request.method == "POST":
        form = CheckoutForm(request.POST)

        # ------------------------------------------------------------
        # 3A) FORM DOĞRULAMA — NEDEN?
        # Form hatalıysa sipariş yazılmaz
        # ------------------------------------------------------------
        if form.is_valid():

            # ========================================================
            # 4) ✅ 2. KAPI: ATOMIC + SELECT_FOR_UPDATE — EN KRİTİK
            # ========================================================
            # transaction.atomic ne yapar?
            # - bu blok içindeki işlemler "tek paket" olur
            # - hata olursa hepsi geri alınır (rollback)
            #
            # select_for_update ne yapar?
            # - ürün satırlarını DB’de kilitler
            # - aynı anda 2 kişi aynı ürünü almaya çalışırsa çakışmayı engeller
            with transaction.atomic():

                # ----------------------------------------------------
                # 4A) ÜRÜNLERİ KİLİTLEYEREK ÇEK (select_for_update)
                # ----------------------------------------------------
                locked_products = Product.objects.select_for_update().filter(
                    id__in=product_ids, is_active=True
                )
                locked_map = {p.id: p for p in locked_products}

                # ----------------------------------------------------
                # 4B) ✅ SON STOK KONTROLÜ (Checkout anı)
                # Sepette stok kontrolü var (1. kapı)
                # Checkout’ta tekrar şart (2. kapı)
                # ----------------------------------------------------
                for row in items:
                    p = locked_map.get(row["product"].id)
                    qty = int(row["quantity"])

                    if p is None:
                        messages.error(request, "Bir ürün bulunamadı. Sepeti kontrol et.")
                        return redirect("cart:detail")

                    if p.stock <= 0:
                        messages.error(request, f"{p.name} tükendi.")
                        return redirect("cart:detail")

                    if qty > p.stock:
                        messages.warning(
                            request,
                            f"{p.name}: stok yetersiz. Maksimum {p.stock} adet alabilirsiniz."
                        )
                        return redirect("cart:detail")

                # ----------------------------------------------------
                # 4C) ✅ ORDER OLUŞTUR (Sipariş başlığı)
                # Order: user + total + form bilgileri (adres/telefon vs.)
                # ----------------------------------------------------
                order = form.save(commit=False)
                order.user = request.user
                order.total = total
                order.save()

                # ====================================================
                # 4D) ✅ ORDERITEM OLUŞTUR (Sipariş satırları) + STOK DÜŞ
                # ====================================================
                # Snapshot mantığı:
                # - sipariş anındaki ürün adı ve fiyatı kaydedilir
                # - yarın fiyat değişse bile geçmiş sipariş bozulmaz
                for row in items:
                    p = locked_map[row["product"].id]
                    qty = int(row["quantity"])

                    OrderItem.objects.create(
                        order=order,
                        product_id=p.id,
                        name=p.name,
                        quantity=qty,
                        unit_price=p.price,
                    )

                    # -------------------------------
                    # ✅ STOK DÜŞ
                    # -------------------------------
                    p.stock -= qty
                    p.save(update_fields=["stock"])

                # ----------------------------------------------------
                # 4E) ✅ SEPETİ TEMİZLE
                # ----------------------------------------------------
                _clear_cart(request.session)

            # --------------------------------------------------------
            # 4F) TRANSACTION DIŞI: BAŞARILI MESAJ + SUCCESS SAYFASI
            # --------------------------------------------------------
            messages.success(request, "Siparişiniz alındı ✅")
            return redirect("orders:success", order_id=order.id)

        # ------------------------------------------------------------
        # 3B) FORM HATALIYSA
        # ------------------------------------------------------------
        messages.error(request, "Form hatalı. Lütfen bilgileri kontrol edin.")

    else:
        # ------------------------------------------------------------
        # 3C) GET: boş form
        # ------------------------------------------------------------
        form = CheckoutForm()

    return render(request, "orders/checkout.html", {
        "form": form,
        "items": items,
        "total": total,
    })


# ============================================================
# 5) SUCCESS — Sipariş başarı sayfası
# ============================================================
@login_required
def success(request, order_id):
    # Güvenlik: kullanıcı sadece kendi siparişini görür
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/success.html", {"order": order})


# ============================================================
# 6) MY ORDERS — Siparişlerim listesi
# ============================================================
@login_required
def my_orders(request):
    # Kullanıcı sadece kendi siparişlerini görür
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": orders})


# ============================================================
# 7) ORDER DETAIL — Sipariş detay sayfası
# ============================================================
@login_required
def order_detail(request, order_id):
    # Güvenlik: sadece kendi siparişi
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


# ============================================================
# 8) CANCEL ORDER — Kullanıcı siparişi iptal eder
# ============================================================



@login_required
@require_POST
@transaction.atomic
def cancel_order(request, order_id):
    # ------------------------------------------------------------
    # 1) Güvenlik: sadece kendi siparişi
    # ------------------------------------------------------------
    order = get_object_or_404(
    Order.objects.select_for_update(),
    id=order_id,
    user=request.user
)


    # ------------------------------------------------------------
    # 2) Kural: sadece pending iken iptal edilir
    # ------------------------------------------------------------
    if order.status != Order.STATUS_PENDING:
        messages.warning(request, "Bu sipariş iptal edilemez (kargoya verilmiş olabilir).")
        return redirect("orders:order_detail", order_id=order.id)

    # ------------------------------------------------------------
    # 3) Stok geri yükleme — select_for_update ile kilitle
    # ------------------------------------------------------------
    # OrderItem’da product_id var (snapshot), o yüzden Product’ı id ile buluyoruz.
    product_ids = [item.product_id for item in order.items.all()]

    locked_products = Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)
    locked_map = {p.id: p for p in locked_products}

    for item in order.items.all():
        p = locked_map.get(item.product_id)

        # Ürün DB'den silinmiş / pasif olmuş olabilir → stok geri koyamayız
        # Ama iptali yine de yapabiliriz (snapshot sayesinde sipariş bozulmaz)
        if p:
            p.stock += int(item.quantity)
            p.save(update_fields=["stock"])

    # ------------------------------------------------------------
    # 4) Sipariş durumunu iptal yap
    # ------------------------------------------------------------
    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=["status"])

    messages.success(request, "Sipariş iptal edildi. Stoklar geri yüklendi ✅")
    return redirect("orders:order_detail", order_id=order.id)
