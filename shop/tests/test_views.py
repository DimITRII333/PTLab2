from decimal import Decimal

from django.test import TestCase, Client

from shop.models import Product, Purchase


class PurchaseCreateTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_webpage_accessibility(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_order_page_accessibility(self):
        response = self.client.get('/order/')
        self.assertEqual(response.status_code, 200)

    def test_buy_page_accessibility(self):
        response = self.client.get(f'/buy/{self.tshirt.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_order_with_different_products_gets_discount(self):
        response = self.client.post('/order/', {
            'person': 'Иванов', 'address': 'ул. Мира',
            f'quantity_{self.tshirt.pk}': 2,
            f'quantity_{self.jeans.pk}': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Спасибо за покупку, Иванов!')
        self.assertEqual(Purchase.objects.get().total, Decimal('5310.00'))
