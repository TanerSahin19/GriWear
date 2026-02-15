# orders/admin.py
from django.contrib import admin
from django.db import transaction
from django.contrib import messages
from catalog.models import Product
from .models import Order, OrderItem


# ============================================================
# 1) Inline: Order açınca alt tarafta OrderItem satırlarını göster
# ============================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# ============================================================
# 2) Actions: Status değiştir
# ============================================================
@admin.action(description="Seçilen siparişleri Hazırlanıyor yap")
def mark_pending(modeladmin, request, queryset):
    queryset.update(status=Order.STATUS_PENDING)


@admin.action(description="Seçilen siparişleri Kargoya Verildi yap")
def mark_shipped(modeladmin, request, queryset):
    queryset.update(status=Order.STATUS_SHIPPED)


@admin.action(description="Seçilen siparişleri Teslim Edildi yap")
def mark_delivered(modeladmin, request, queryset):
    queryset.update(status=Order.STATUS_DELIVERED)


# ============================================================
# 3) Cancel + Stock: Toplu iptal (stok geri yüklemeli)
# ============================================================
@admin.action(description="Seçilen siparişleri İptal Et (stokları geri yükle)")
@transaction.atomic
def cancel_orders_with_stock(modeladmin, request, queryset):
    pending_orders = queryset.filter(status=Order.STATUS_PENDING)

    if not pending_orders.exists():
        messages.warning(request, "İptal edilebilir (pending) sipariş bulunamadı.")
        return

    order_ids = list(pending_orders.values_list("id", flat=True))
    items = OrderItem.objects.filter(order_id__in=order_ids)

    product_ids = list(items.values_list("product_id", flat=True).distinct())
    locked_products = Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)
    locked_map = {p.id: p for p in locked_products}

    for item in items:
        p = locked_map.get(item.product_id)
        if p:
            p.stock += int(item.quantity)
            p.save(update_fields=["stock"])

    updated_count = pending_orders.update(status=Order.STATUS_CANCELLED)
    messages.success(request, f"{updated_count} sipariş iptal edildi. Stoklar geri yüklendi ✅")


# ============================================================
# 4) Order Admin
# ============================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "full_name", "phone")
    inlines = [OrderItemInline]
    actions = [mark_pending, mark_shipped, mark_delivered, cancel_orders_with_stock]
