from datetime import datetime

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

    def test_correctness_data(self):
        purchase = Purchase.objects.get(pk=self.purchase.pk)
        self.assertTrue(purchase.person == "Ivanov")
        self.assertTrue(purchase.address == "Svetlaya St.")
        self.assertTrue(purchase.date.replace(microsecond=0) ==
                        self.datetime.replace(microsecond=0))

    def test_items(self):
        item = self.purchase.items.get()
        self.assertEqual(item.product, self.product_book)
        self.assertEqual(item.cost, 1480)
