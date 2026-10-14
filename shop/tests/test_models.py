from datetime import datetime
from decimal import Decimal

from django.db.models import ProtectedError
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


class ModelsBehaviourTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.purchase = Purchase.objects.create(person="Иванов",
                                                address="ул. Мира")
        self.item = PurchaseItem.objects.create(purchase=self.purchase,
                                                product=self.tshirt,
                                                quantity=3, price=1200)

    def test_product_str(self):
        self.assertEqual(str(self.tshirt), "Футболка (1200 руб.)")

    def test_purchase_str(self):
        self.assertEqual(str(self.purchase),
                         f"Заказ №{self.purchase.pk} от Иванов")

    def test_item_str(self):
        self.assertEqual(str(self.item), "Футболка x 3")

    def test_item_cost(self):
        self.assertEqual(self.item.cost, 3600)

    def test_item_cost_uses_stored_price(self):
        self.tshirt.price = 1
        self.tshirt.save()
        self.item.refresh_from_db()
        self.assertEqual(self.item.cost, 3600)

    def test_deleting_purchase_deletes_items(self):
        self.purchase.delete()
        self.assertEqual(PurchaseItem.objects.count(), 0)
        self.assertTrue(Product.objects.filter(pk=self.tshirt.pk).exists())

    def test_product_in_purchase_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.tshirt.delete()

    def test_product_without_purchases_can_be_deleted(self):
        hat = Product.objects.create(name="Шапка", price=900)
        hat.delete()
        self.assertFalse(Product.objects.filter(name="Шапка").exists())

    def test_purchase_items_related_name(self):
        PurchaseItem.objects.create(purchase=self.purchase,
                                    product=self.tshirt,
                                    quantity=1, price=1200)
        self.assertEqual(self.purchase.items.count(), 2)
