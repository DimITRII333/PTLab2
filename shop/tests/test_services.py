from decimal import Decimal

from django.test import TestCase

from shop.models import Product, Purchase
from shop.services import (calculate_order, create_purchase,
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
