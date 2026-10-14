from decimal import Decimal
from unittest import mock

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase

from shop.models import Product, Purchase, PurchaseItem
from shop.services import (DISCOUNT_PERCENT, MIN_DISTINCT_PRODUCTS,
                           OrderSummary, calculate_order, create_purchase,
                           is_discount_applicable)


class CalculateOrderTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_single_product_has_no_discount(self):
        summary = calculate_order([(self.tshirt, 3)])
        self.assertEqual(summary.subtotal, Decimal('3600'))
        self.assertEqual(summary.discount, Decimal('0'))
        self.assertEqual(summary.total, Decimal('3600'))
        self.assertFalse(summary.has_discount)

    def test_different_products_get_ten_percent_discount(self):
        summary = calculate_order([(self.tshirt, 2), (self.jeans, 1)])
        self.assertEqual(summary.subtotal, Decimal('5900'))
        self.assertEqual(summary.discount, Decimal('590.00'))
        self.assertEqual(summary.total, Decimal('5310.00'))
        self.assertTrue(summary.has_discount)

    def test_zero_quantity_is_ignored(self):
        self.assertFalse(is_discount_applicable(
            [(self.tshirt, 1), (self.jeans, 0)]))


class CreatePurchaseTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_purchase_with_discount_is_saved(self):
        purchase = create_purchase("Иванов", "ул. Мира",
                                   [(self.tshirt, 2), (self.jeans, 1)])
        purchase.refresh_from_db()
        self.assertEqual(purchase.total, Decimal('5310.00'))
        self.assertEqual(purchase.items.count(), 2)

    def test_empty_purchase_is_rejected(self):
        with self.assertRaises(ValueError):
            create_purchase("Иванов", "ул. Мира", [(self.tshirt, 0)])
        self.assertEqual(Purchase.objects.count(), 0)


def fake_product(pk, price):
    """Мок товара: сервис использует только pk и price, БД не нужна."""
    return mock.Mock(spec=Product, pk=pk, price=price)


class DiscountRuleTestCase(SimpleTestCase):
    """Проверка правила скидки на мок-объектах без обращения к БД."""

    def setUp(self):
        self.a = fake_product(1, 1000)
        self.b = fake_product(2, 500)
        self.c = fake_product(3, 205)

    def test_constants_match_variant(self):
        self.assertEqual(DISCOUNT_PERCENT, Decimal('10'))
        self.assertEqual(MIN_DISTINCT_PRODUCTS, 2)

    def test_empty_order(self):
        summary = calculate_order([])
        self.assertEqual(summary, OrderSummary(Decimal('0'), Decimal('0'),
                                               Decimal('0')))
        self.assertFalse(is_discount_applicable([]))

    def test_only_zero_quantities(self):
        summary = calculate_order([(self.a, 0), (self.b, 0)])
        self.assertEqual(summary.total, Decimal('0'))
        self.assertFalse(summary.has_discount)

    def test_many_items_of_one_product_have_no_discount(self):
        summary = calculate_order([(self.a, 10)])
        self.assertEqual(summary.total, Decimal('10000'))
        self.assertFalse(summary.has_discount)

    def test_same_product_listed_twice_has_no_discount(self):
        summary = calculate_order([(self.a, 1), (self.a, 2)])
        self.assertEqual(summary.subtotal, Decimal('3000'))
        self.assertEqual(summary.discount, Decimal('0'))

    def test_two_different_products(self):
        summary = calculate_order([(self.a, 1), (self.b, 1)])
        self.assertEqual(summary.discount, Decimal('150.00'))
        self.assertEqual(summary.total, Decimal('1350.00'))

    def test_three_different_products(self):
        summary = calculate_order([(self.a, 1), (self.b, 2), (self.c, 3)])
        self.assertEqual(summary.subtotal, Decimal('2615'))
        self.assertEqual(summary.discount, Decimal('261.50'))
        self.assertEqual(summary.total, Decimal('2353.50'))

    def test_discount_applies_to_whole_sum(self):
        summary = calculate_order([(self.a, 5), (self.b, 1)])
        self.assertEqual(summary.discount, summary.subtotal / 10)

    def test_amounts_have_two_decimal_places(self):
        summary = calculate_order([(self.a, 1), (self.c, 1)])
        for amount in (summary.subtotal, summary.discount, summary.total):
            self.assertEqual(amount.as_tuple().exponent, -2)
        self.assertEqual(summary.discount, Decimal('120.50'))

    def test_total_equals_subtotal_minus_discount(self):
        summary = calculate_order([(self.a, 3), (self.c, 7)])
        self.assertEqual(summary.total, summary.subtotal - summary.discount)

    def test_negative_quantity_raises(self):
        with self.assertRaises(ValueError):
            calculate_order([(self.a, 1), (self.b, -1)])
        with self.assertRaises(ValueError):
            is_discount_applicable([(self.a, -1)])

    def test_accepts_generator(self):
        summary = calculate_order(p for p in [(self.a, 1), (self.b, 1)])
        self.assertTrue(summary.has_discount)

    def test_summary_is_immutable(self):
        summary = calculate_order([(self.a, 1)])
        with self.assertRaises(AttributeError):
            summary.total = Decimal('1')


class CreatePurchaseEdgeCasesTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_purchase_without_discount_is_saved(self):
        purchase = create_purchase("Петров", "пр. Ленина", [(self.jeans, 2)])
        purchase.refresh_from_db()
        self.assertEqual(purchase.subtotal, Decimal('7000'))
        self.assertEqual(purchase.discount, Decimal('0'))
        self.assertEqual(purchase.total, Decimal('7000'))

    def test_items_store_quantity_and_price(self):
        purchase = create_purchase("Иванов", "ул. Мира",
                                   [(self.tshirt, 2), (self.jeans, 1)])
        items = {i.product_id: i for i in purchase.items.all()}
        self.assertEqual(items[self.tshirt.pk].quantity, 2)
        self.assertEqual(items[self.tshirt.pk].price, 1200)
        self.assertEqual(items[self.jeans.pk].quantity, 1)

    def test_zero_quantity_items_are_not_saved(self):
        purchase = create_purchase("Иванов", "ул. Мира",
                                   [(self.tshirt, 1), (self.jeans, 0)])
        self.assertEqual(purchase.items.count(), 1)
        self.assertEqual(purchase.discount, Decimal('0'))

    def test_item_price_does_not_change_with_product_price(self):
        purchase = create_purchase("Иванов", "ул. Мира", [(self.tshirt, 1)])
        self.tshirt.price = 9999
        self.tshirt.save()
        item = purchase.items.get()
        self.assertEqual(item.price, 1200)
        purchase.refresh_from_db()
        self.assertEqual(purchase.total, Decimal('1200'))

    def test_empty_items_list_is_rejected(self):
        with self.assertRaises(ValueError):
            create_purchase("Иванов", "ул. Мира", [])
        self.assertEqual(Purchase.objects.count(), 0)

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(ValueError):
            create_purchase("Иванов", "ул. Мира", [(self.tshirt, -2)])
        self.assertEqual(Purchase.objects.count(), 0)

    def test_transaction_rolls_back_on_items_error(self):
        with mock.patch.object(PurchaseItem.objects, 'bulk_create',
                               side_effect=DatabaseError("db failure")):
            with self.assertRaises(DatabaseError):
                create_purchase("Иванов", "ул. Мира",
                                [(self.tshirt, 1), (self.jeans, 1)])
        self.assertEqual(Purchase.objects.count(), 0)
        self.assertEqual(PurchaseItem.objects.count(), 0)
