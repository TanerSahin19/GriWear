def cart_count(request):
    cart = request.session.get("cart", {})  # senin CART_SESSION_KEY "cart"
    count = sum(item.get("qty", 0) for item in cart.values())
    return {"cart_count": count}
