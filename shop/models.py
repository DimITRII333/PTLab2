from decimal import Decimal

from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.name} ({self.price} руб.)'


class Purchase(models.Model):
    """Заказ покупателя, может содержать несколько позиций (PurchaseItem)."""
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2,
                                   default=Decimal('0'))
    discount = models.DecimalField(max_digits=12, decimal_places=2,
                                   default=Decimal('0'))
    total = models.DecimalField(max_digits=12, decimal_places=2,
                                default=Decimal('0'))

    def __str__(self):
        return f'Заказ №{self.pk} от {self.person}'


class PurchaseItem(models.Model):
    """Позиция заказа: товар, количество и цена на момент покупки."""
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE,
                                 related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()

    @property
    def cost(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
