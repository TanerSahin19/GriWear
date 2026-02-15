from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    # Category model
    def get_absolute_url(self):
     return reverse("catalog:category_products", args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_new = models.BooleanField(default=False)

    image = models.ImageField(upload_to="products/", blank=True, null=True)  # şimdilik opsiyonel
    description = models.TextField(blank=True)
    stock = models.PositiveIntegerField(default=0)


    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    # Product model
def get_absolute_url(self):
    return reverse("catalog:product_detail", args=[self.slug])
