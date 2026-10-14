from django.test import TestCase

from shop.form import PurchaseForm
from shop.models import Product


class PurchaseFormTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200,
                                             stock=5)

    def test_valid_form(self):
        form = PurchaseForm(data={'person': 'Иванов', 'address': 'ул. Мира',
                                  f'quantity_{self.tshirt.pk}': '2'})
        self.assertTrue(form.is_valid())

    def test_no_products_selected(self):
        form = PurchaseForm(data={'person': 'Иванов', 'address': 'ул. Мира',
                                  f'quantity_{self.tshirt.pk}': '0'})
        self.assertFalse(form.is_valid())

    def test_negative_quantity(self):
        form = PurchaseForm(data={'person': 'Иванов', 'address': 'ул. Мира',
                                  f'quantity_{self.tshirt.pk}': '-1'})
        self.assertFalse(form.is_valid())

    def test_quantity_more_than_stock(self):
        form = PurchaseForm(data={'person': 'Иванов', 'address': 'ул. Мира',
                                  f'quantity_{self.tshirt.pk}': '6'})
        self.assertFalse(form.is_valid())
