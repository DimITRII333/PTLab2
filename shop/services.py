"""Бизнес-логика магазина одежды (вариант 10).

При одновременной покупке товаров разного вида (не менее двух разных
товаров в одном заказе) на общую сумму покупки предоставляется скидка 10%.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.db import transaction

from .models import Product, Purchase, PurchaseItem

DISCOUNT_PERCENT = Decimal('10')
MIN_DISTINCT_PRODUCTS = 2
MONEY_STEP = Decimal('0.01')

OrderItems = Iterable[tuple[Product, int]]


@dataclass(frozen=True)
class OrderSummary:
    subtotal: Decimal
    discount: Decimal
    total: Decimal

    @property
    def has_discount(self) -> bool:
        return self.discount > 0


def _positions(items: OrderItems) -> list[tuple[Product, int]]:
    """Оставляет только позиции с ненулевым количеством."""
    positions = []
    for product, quantity in items:
        if quantity < 0:
            raise ValueError(f'Отрицательное количество товара: {product}')
        if quantity > 0:
            positions.append((product, quantity))
    return positions


def is_discount_applicable(items: OrderItems) -> bool:
    distinct_products = {product.pk for product, _ in _positions(items)}
    return len(distinct_products) >= MIN_DISTINCT_PRODUCTS


def calculate_order(items: OrderItems) -> OrderSummary:
    positions = _positions(items)
    subtotal = sum((Decimal(product.price) * quantity
                    for product, quantity in positions),
                   Decimal('0')).quantize(MONEY_STEP)
    discount = Decimal('0').quantize(MONEY_STEP)
    if is_discount_applicable(positions):
        discount = (subtotal * DISCOUNT_PERCENT / 100).quantize(
            MONEY_STEP, rounding=ROUND_HALF_UP)
    return OrderSummary(subtotal=subtotal, discount=discount,
                        total=subtotal - discount)


@transaction.atomic
def create_purchase(person: str, address: str,
                    items: OrderItems) -> Purchase:
    positions = _positions(items)
    if not positions:
        raise ValueError('Заказ должен содержать хотя бы один товар')
    summary = calculate_order(positions)
    purchase = Purchase.objects.create(
        person=person, address=address,
        subtotal=summary.subtotal, discount=summary.discount,
        total=summary.total)
    PurchaseItem.objects.bulk_create([
        PurchaseItem(purchase=purchase, product=product,
                     quantity=quantity, price=product.price)
        for product, quantity in positions
    ])
    return purchase
