from django.contrib.auth.models import User
from django.test import TestCase

from shop.models import Product


class AdminTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('admin', 'a@a.ru', 'pass')
        self.client.force_login(user)
        Product.objects.create(name="Футболка", price=1200, stock=25)
        Product.objects.create(name="Кроссовки", price=5400, stock=0)

    def test_products_page(self):
        response = self.client.get('/admin/shop/product/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Остаток на складе')

    def test_filter_out_of_stock(self):
        response = self.client.get('/admin/shop/product/?stock=out')
        self.assertContains(response, 'Кроссовки')
        self.assertNotContains(response, 'Футболка')
