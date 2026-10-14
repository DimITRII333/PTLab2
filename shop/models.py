from decimal import Decimal

from django.db import models


class Product(models.Model):
    DEFAULT_STOCK = 100

    name = models.CharField('Наименование', max_length=200)
    price = models.PositiveIntegerField('Цена, руб.')
    stock = models.PositiveIntegerField('Остаток на складе, шт.',
                                        default=DEFAULT_STOCK)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return f'{self.name} ({self.price} руб.)'


class Purchase(models.Model):
    """Заказ покупателя, может содержать несколько позиций (PurchaseItem)."""

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    person = models.CharField('Покупатель', max_length=200)
    address = models.CharField('Адрес доставки', max_length=200)
    date = models.DateTimeField('Дата', auto_now_add=True)
    subtotal = models.DecimalField('Сумма', max_digits=12, decimal_places=2,
                                   default=Decimal('0'))
    discount = models.DecimalField('Скидка', max_digits=12, decimal_places=2,
                                   default=Decimal('0'))
    total = models.DecimalField('Итого', max_digits=12, decimal_places=2,
                                default=Decimal('0'))

    def __str__(self):
        return f'Заказ №{self.pk} от {self.person}'


class PurchaseItem(models.Model):
    """Позиция заказа: товар, количество и цена на момент покупки."""

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE,
                                 related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT,
                                verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество')
    price = models.PositiveIntegerField('Цена, руб.')

    @property
    def cost(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
