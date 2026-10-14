"""Бизнес-логика магазина одежды (вариант 10).

При одновременной покупке товаров разного вида (не менее двух разных
товаров в одном заказе) на общую сумму покупки предоставляется скидка 10%.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from django.db import transaction
from django.db.models import F

from .models import Product, Purchase, PurchaseItem

DISCOUNT_PERCENT = Decimal('10')
MIN_DISTINCT_PRODUCTS = 2
MONEY_STEP = Decimal('0.01')

OrderItems = Iterable[tuple[Product, int]]


class OutOfStockError(ValueError):
    """На складе недостаточно товара для оформления заказа."""


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
    _reserve_stock(positions)
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


def _reserve_stock(positions: list[tuple[Product, int]]) -> None:
    """Проверяет остатки и списывает купленное количество со склада.
    Строки товаров блокируются (select_for_update), чтобы два
    одновременных заказа не продали один и тот же остаток."""
    needed: dict[int, int] = {}
    for product, quantity in positions:
        needed[product.pk] = needed.get(product.pk, 0) + quantity
    locked = Product.objects.select_for_update().in_bulk(needed.keys())
    for pk, quantity in needed.items():
        product = locked[pk]
        if product.stock < quantity:
            raise OutOfStockError(
                f'Недостаточно товара «{product.name}»: '
                f'в наличии {product.stock} шт., запрошено {quantity} шт.')
    for pk, quantity in needed.items():
        Product.objects.filter(pk=pk).update(stock=F('stock') - quantity)
