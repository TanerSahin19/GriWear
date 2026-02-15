from .models import Order

def orders_count(request):
    """
    NEDEN?
    - Navbar her sayfada görünüyor.
    - Her sayfada "Siparişlerim (sayı)" göstermek için
      bu sayıyı global template context'e basarız.

    KURAL:
    - Login değilse: 0
    - Login ise: sadece kullanıcının sipariş sayısı
    """
    if request.user.is_authenticated:
        return {
            "orders_count": Order.objects.filter(user=request.user).count()
        }
    return {"orders_count": 0}
