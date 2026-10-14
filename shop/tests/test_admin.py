from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from shop.admin import ProductAdmin, PurchaseAdmin, PurchaseItemInline
from shop.models import Product, Purchase, PurchaseItem


class AdminRegistrationTestCase(TestCase):
    def test_models_registered(self):
        self.assertIsInstance(admin.site._registry[Product], ProductAdmin)
        self.assertIsInstance(admin.site._registry[Purchase], PurchaseAdmin)

    def test_purchase_admin_has_items_inline(self):
        self.assertIn(PurchaseItemInline, PurchaseAdmin.inlines)
        self.assertEqual(PurchaseItemInline.model, PurchaseItem)

    def test_purchase_list_display_shows_amounts(self):
        for field in ('subtotal', 'discount', 'total'):
            self.assertIn(field, PurchaseAdmin.list_display)


class AdminPagesTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_superuser('admin', 'a@a.ru', 'pass')
        self.client.force_login(user)
        product = Product.objects.create(name="Футболка", price=1200)
        self.purchase = Purchase.objects.create(person="Иванов",
                                                address="ул. Мира")
        PurchaseItem.objects.create(purchase=self.purchase, product=product,
                                    quantity=1, price=1200)

    def test_product_changelist(self):
        response = self.client.get('/admin/shop/product/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Футболка")

    def test_purchase_change_page_shows_items(self):
        response = self.client.get(
            f'/admin/shop/purchase/{self.purchase.pk}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "items-TOTAL_FORMS")

    def test_admin_requires_login(self):
        self.client.logout()
        response = self.client.get('/admin/shop/purchase/')
        self.assertEqual(response.status_code, 302)
