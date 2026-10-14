from decimal import Decimal

from django.test import TestCase

from shop.form import MAX_QUANTITY, PurchaseForm
from shop.models import Product, Purchase


class PurchaseFormTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def make_data(self, **quantities):
        data = {'person': 'Иванов', 'address': 'ул. Мира'}
        data.update(quantities)
        return data

    def qty(self, product):
        return PurchaseForm.quantity_field_name(product)

    def test_quantity_field_name(self):
        self.assertEqual(PurchaseForm.quantity_field_name(self.tshirt),
                         f'quantity_{self.tshirt.pk}')

    def test_fields_created_for_every_product(self):
        form = PurchaseForm()
        self.assertIn('person', form.fields)
        self.assertIn('address', form.fields)
        self.assertIn(self.qty(self.tshirt), form.fields)
        self.assertIn(self.qty(self.jeans), form.fields)
        self.assertEqual(form.fields[self.qty(self.tshirt)].label,
                         "Футболка")

    def test_products_are_ordered_by_pk(self):
        self.assertEqual(PurchaseForm().products, [self.tshirt, self.jeans])

    def test_explicit_products_limit_fields(self):
        form = PurchaseForm(products=[self.jeans])
        self.assertNotIn(self.qty(self.tshirt), form.fields)
        self.assertIn(self.qty(self.jeans), form.fields)

    def test_initial_quantity_default_is_zero(self):
        form = PurchaseForm()
        self.assertEqual(form.fields[self.qty(self.tshirt)].initial, 0)
        self.assertEqual(form.fields[self.qty(self.jeans)].initial, 0)

    def test_initial_product_is_preselected(self):
        form = PurchaseForm(initial_product_id=self.jeans.pk)
        self.assertEqual(form.fields[self.qty(self.tshirt)].initial, 0)
        self.assertEqual(form.fields[self.qty(self.jeans)].initial, 1)

    def test_quantity_fields_pairs(self):
        form = PurchaseForm()
        pairs = form.quantity_fields()
        self.assertEqual([product for product, _ in pairs],
                         [self.tshirt, self.jeans])
        self.assertEqual(pairs[0][1].name, self.qty(self.tshirt))

    def test_valid_form(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '2', self.qty(self.jeans): '1'}))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_items(),
                         [(self.tshirt, 2), (self.jeans, 1)])

    def test_missing_quantity_treated_as_zero(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '3'}))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.get_items(),
                         [(self.tshirt, 3), (self.jeans, 0)])

    def test_no_products_selected_is_invalid(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '0', self.qty(self.jeans): ''}))
        self.assertFalse(form.is_valid())
        self.assertIn('Выберите хотя бы один товар для покупки.',
                      form.non_field_errors())

    def test_negative_quantity_is_invalid(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '-1', self.qty(self.jeans): '1'}))
        self.assertFalse(form.is_valid())
        self.assertIn(self.qty(self.tshirt), form.errors)

    def test_quantity_above_maximum_is_invalid(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): str(MAX_QUANTITY + 1)}))
        self.assertFalse(form.is_valid())
        self.assertIn(self.qty(self.tshirt), form.errors)

    def test_maximum_quantity_is_valid(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): str(MAX_QUANTITY)}))
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_integer_quantity_is_invalid(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): 'два'}))
        self.assertFalse(form.is_valid())
        self.assertIn(self.qty(self.tshirt), form.errors)

    def test_person_and_address_are_required(self):
        form = PurchaseForm(data={self.qty(self.tshirt): '1'})
        self.assertFalse(form.is_valid())
        self.assertIn('person', form.errors)
        self.assertIn('address', form.errors)

    def test_person_max_length(self):
        data = self.make_data(**{self.qty(self.tshirt): '1'})
        data['person'] = 'x' * 201
        form = PurchaseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('person', form.errors)

    def test_save_creates_purchase_with_discount(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '2', self.qty(self.jeans): '1'}))
        self.assertTrue(form.is_valid(), form.errors)
        purchase = form.save()
        self.assertEqual(Purchase.objects.count(), 1)
        self.assertEqual(purchase.person, 'Иванов')
        self.assertEqual(purchase.address, 'ул. Мира')
        self.assertEqual(purchase.discount, Decimal('590.00'))
        self.assertEqual(purchase.items.count(), 2)

    def test_save_skips_zero_quantities(self):
        form = PurchaseForm(data=self.make_data(
            **{self.qty(self.tshirt): '1', self.qty(self.jeans): '0'}))
        self.assertTrue(form.is_valid(), form.errors)
        purchase = form.save()
        self.assertEqual(list(purchase.items.values_list(
            'product__name', flat=True)), ["Футболка"])
        self.assertEqual(purchase.discount, Decimal('0'))
