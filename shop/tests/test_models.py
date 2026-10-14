from datetime import datetime
from decimal import Decimal

from django.test import TestCase

from shop.models import Product, Purchase, PurchaseItem


class ProductTestCase(TestCase):
    def setUp(self):
        Product.objects.create(name="book", price="740")
        Product.objects.create(name="pencil", price="50")

    def test_correctness_types(self):
        self.assertIsInstance(Product.objects.get(name="book").name, str)
        self.assertIsInstance(Product.objects.get(name="book").price, int)
        self.assertIsInstance(Product.objects.get(name="pencil").name, str)
        self.assertIsInstance(Product.objects.get(name="pencil").price, int)

    def test_correctness_data(self):
        self.assertTrue(Product.objects.get(name="book").price == 740)
        self.assertTrue(Product.objects.get(name="pencil").price == 50)


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.product_book = Product.objects.create(name="book", price="740")
        self.datetime = datetime.now()
        self.purchase = Purchase.objects.create(person="Ivanov",
                                                address="Svetlaya St.")
        PurchaseItem.objects.create(purchase=self.purchase,
                                    product=self.product_book,
                                    quantity=2, price=740)

    def test_correctness_types(self):
        purchase = Purchase.objects.get(pk=self.purchase.pk)
        self.assertIsInstance(purchase.person, str)
        self.assertIsInstance(purchase.address, str)
        self.assertIsInstance(purchase.date, datetime)
        self.assertIsInstance(purchase.total, Decimal)

    def test_correctness_data(self):
        purchase = Purchase.objects.get(pk=self.purchase.pk)
        self.assertTrue(purchase.person == "Ivanov")
        self.assertTrue(purchase.address == "Svetlaya St.")
        self.assertTrue(purchase.date.replace(microsecond=0) ==
                        self.datetime.replace(microsecond=0))

    def test_default_amounts_are_zero(self):
        purchase = Purchase.objects.get(pk=self.purchase.pk)
        self.assertEqual(purchase.subtotal, Decimal('0'))
        self.assertEqual(purchase.discount, Decimal('0'))
        self.assertEqual(purchase.total, Decimal('0'))

    def test_items_relation(self):
        item = self.purchase.items.get()
        self.assertEqual(item.product, self.product_book)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.cost, 1480)
