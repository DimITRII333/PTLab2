from decimal import Decimal

from django.test import TestCase

from shop.models import Product, Purchase
from shop.services import OutOfStockError, calculate_order, create_purchase


class CalculateOrderTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_one_product_no_discount(self):
        summary = calculate_order([(self.tshirt, 3)])
        self.assertEqual(summary.discount, 0)
        self.assertEqual(summary.total, 3600)

    def test_different_products_discount(self):
        summary = calculate_order([(self.tshirt, 2), (self.jeans, 1)])
        self.assertEqual(summary.subtotal, 5900)
        self.assertEqual(summary.discount, Decimal('590'))
        self.assertEqual(summary.total, Decimal('5310'))

    def test_zero_quantity_is_ignored(self):
        summary = calculate_order([(self.tshirt, 1), (self.jeans, 0)])
        self.assertEqual(summary.discount, 0)


class CreatePurchaseTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200,
                                             stock=5)
        self.jeans = Product.objects.create(name="Джинсы", price=3500,
                                            stock=2)

    def test_purchase_is_saved(self):
        purchase = create_purchase("Иванов", "ул. Мира",
                                   [(self.tshirt, 2), (self.jeans, 1)])
        self.assertEqual(purchase.total, Decimal('5310'))
        self.assertEqual(purchase.items.count(), 2)

    def test_empty_purchase(self):
        with self.assertRaises(ValueError):
            create_purchase("Иванов", "ул. Мира", [(self.tshirt, 0)])

    def test_stock_decreases(self):
        create_purchase("Иванов", "ул. Мира", [(self.tshirt, 3)])
        self.tshirt.refresh_from_db()
        self.assertEqual(self.tshirt.stock, 2)

    def test_not_enough_stock(self):
        with self.assertRaises(OutOfStockError):
            create_purchase("Иванов", "ул. Мира", [(self.jeans, 3)])
        self.assertEqual(Purchase.objects.count(), 0)
