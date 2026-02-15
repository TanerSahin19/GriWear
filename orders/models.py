# ============================================================
# orders/models.py  —  GRİWEAR (KİLİTLİ)
# Konu: Sipariş (Order) + Sipariş Satırı (OrderItem)
# Amaç: Checkout’tan sonra siparişin DB’de kalıcı kaydı
# ============================================================

from django.db import models
from django.conf import settings


# ============================================================
# 1) ORDER MODELİ — “SİPARİŞİN BAŞLIĞI / KİMLİĞİ”
# ============================================================
# Order ne demek?
# - Siparişin ana kaydı.
# - Kime ait, adresi ne, toplam kaç para, durumu ne?
# - Siparişin “üst başlığı”.
#
# Örnek:
# Order #9
# user = gri_kurt
# full_name = Taner Şahin
# total = 667.32
# status = pending / shipped / delivered
# created_at = ...
#
class Order(models.Model):

    # ------------------------------------------------------------
    # 1A) STATUS SABİTLERİ — NEDEN?
    # ------------------------------------------------------------
    # status için "serbest yazı" kullanırsak admin yanlış yazabilir:
    # "pendng", "kargo", "teslim" gibi hatalar olur.
    # Bu yüzden sabit değer + choices kullanıyoruz.
    STATUS_PENDING = "pending"      # sipariş hazırlandı / hazırlanıyor
    STATUS_SHIPPED = "shipped"      # kargoya verildi
    STATUS_DELIVERED = "delivered"  # teslim edildi
    STATUS_CANCELLED = "cancelled"  # ✅ yeni
    # ------------------------------------------------------------
    # 1B) STATUS_CHOICES — KULLANICIYA GÖSTERİLECEK ETİKET
    # ------------------------------------------------------------
    # Sol taraf: DB’ye yazılacak gerçek değer (pending)
    # Sağ taraf: ekranda görünen isim (Hazırlanıyor)
    STATUS_CHOICES = [
        (STATUS_PENDING, "Hazırlanıyor"),
        (STATUS_SHIPPED, "Kargoya Verildi"),
        (STATUS_DELIVERED, "Teslim Edildi"),
        (STATUS_CANCELLED, "İptal Edildi"),  # ✅ yeni
    ]
    
    def status_badge_class(self):
        return {
            self.STATUS_PENDING: "text-bg-warning",   # Sarı
            self.STATUS_SHIPPED: "text-bg-primary",   # Mavi
            self.STATUS_DELIVERED: "text-bg-success", # Yeşil
            self.STATUS_CANCELLED: "text-bg-secondary" # Gri
        }.get(self.status, "text-bg-dark")  # Beklenmeyen olursa

    # =========================================================
    # STATUS LABEL — NEDEN?
    # İstersek get_status_display yerine bunu da kullanabiliriz.
    # Şimdilik opsiyonel; display zaten var.
    # =========================================================
    def status_label(self):
        return self.get_status_display()


    # ------------------------------------------------------------
    # 1C) USER — SİPARİŞ KİMİN?
    # ------------------------------------------------------------
    # settings.AUTH_USER_MODEL kullanmak doğru:
    # - custom user olursa bile bozulmaz
    #
    # null=True, blank=True neden?
    # - İleride “misafir sipariş” gibi bir senaryo için kapı bırakır
    # on_delete=SET_NULL neden?
    # - kullanıcı silinse bile sipariş kaydı kaybolmasın, user null olsun
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------
    # 1D) TESLİMAT BİLGİLERİ — NEDEN?
    # ------------------------------------------------------------
    # checkout formundan gelen bilgiler buraya yazılır.
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField()

    # ------------------------------------------------------------
    # 1E) TOTAL — SİPARİŞ TOPLAMI
    # ------------------------------------------------------------
    # checkout view hesaplar, buraya yazar.
    # DecimalField kullanmak şart: para float olmaz.
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ------------------------------------------------------------
    # 1F) STATUS — SİPARİŞ DURUMU
    # ------------------------------------------------------------
    # default=STATUS_PENDING:
    # - yeni sipariş otomatik "Hazırlanıyor" başlar
    #
    # (İsteğe bağlı profesyonel dokunuş):
    # db_index=True -> status’a göre filtre hızlanır
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        # db_index=True,   # istersen aç (opsiyonel)
    )

    # ------------------------------------------------------------
    # 1G) created_at — SİPARİŞ TARİHİ
    # ------------------------------------------------------------
    # auto_now_add: kayıt ilk oluştuğunda otomatik zaman basar
    created_at = models.DateTimeField(auto_now_add=True)

    # ------------------------------------------------------------
    # 1H) __str__ — ADMIN'DE OKUNUR GÖRÜNSÜN
    # ------------------------------------------------------------
    def __str__(self):
        return f"Order #{self.id}"


# ============================================================
# 2) ORDERITEM MODELİ — “SİPARİŞ SATIRLARI”
# ============================================================
# OrderItem ne demek?
# - Siparişin içindeki ürün satırları.
#
# Örnek:
# Order #9 içinde:
#   - "Kol Düğmesi" qty=2 unit_price=2670.00
#
class OrderItem(models.Model):

    # ------------------------------------------------------------
    # 2A) order FOREIGNKEY — BU SATIR HANGİ SİPARİŞE AİT?
    # ------------------------------------------------------------
    # related_name="items" ne işe yarar?
    # - order.items.all() diyebilmek için
    #   (template’te kullandık)
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )

    # ------------------------------------------------------------
    # 2B) SNAPSHOT ALANLARI — NEDEN ÇOK ÖNEMLİ?
    # ------------------------------------------------------------
    # Normalde ürün tablosuna bağlı kalsaydık:
    # - ürün adı değişir
    # - fiyat değişir
    # eski siparişler bozulurdu.
    #
    # Bu yüzden sipariş anındaki veriyi “kopya” olarak burada saklıyoruz.
    # product_id: ürün silinse bile sipariş satırı bozulmasın
    product_id = models.IntegerField()

    # name: sipariş anındaki ürün adı
    name = models.CharField(max_length=200)

    # quantity: sipariş edilen adet
    quantity = models.PositiveIntegerField(default=1)

    # unit_price: sipariş anındaki birim fiyat (snapshot)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ------------------------------------------------------------
    # 2C) line_total — SATIR TOPLAMI (FİYAT * ADET)
    # ------------------------------------------------------------
    # property ne demek?
    # - DB alanı değildir
    # - hesaplanan değer döndürür
    # - template’te kolaylık sağlar
    @property
    def line_total(self):
        return self.unit_price * self.quantity

    # ------------------------------------------------------------
    # 2D) __str__
    # ------------------------------------------------------------
    def __str__(self):
        return f"{self.name} x{self.quantity}"
