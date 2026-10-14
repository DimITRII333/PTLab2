from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

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


class IndexViewTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def test_uses_index_template(self):
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'shop/index.html')

    def test_lists_all_products(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(list(response.context['products']),
                         [self.tshirt, self.jeans])
        self.assertContains(response, "Футболка")
        self.assertContains(response, "3500")

    def test_contains_buy_and_order_links(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, reverse('buy', args=[self.tshirt.pk]))
        self.assertContains(response, reverse('order'))

    def test_shows_discount_conditions(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['discount_percent'], 10)
        self.assertEqual(response.context['min_distinct_products'], 2)
        self.assertContains(response, "скидка 10%")

    def test_empty_catalog(self):
        Product.objects.all().delete()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)


class PurchaseFormViewTestCase(TestCase):
    def setUp(self):
        self.tshirt = Product.objects.create(name="Футболка", price=1200)
        self.jeans = Product.objects.create(name="Джинсы", price=3500)

    def post_order(self, url=None, **quantities):
        data = {'person': 'Иванов', 'address': 'ул. Мира'}
        data.update({f'quantity_{product.pk}': qty
                     for product, qty in quantities.get('items', [])})
        return self.client.post(url or reverse('order'), data)

    def test_order_page_uses_form_template(self):
        response = self.client.get(reverse('order'))
        self.assertTemplateUsed(response, 'shop/purchase_form.html')
        self.assertContains(response, 'name="quantity_%d"' % self.tshirt.pk)
        self.assertContains(response, 'name="person"')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_order_page_has_nothing_preselected(self):
        form = self.client.get(reverse('order')).context['form']
        self.assertEqual(form.fields[f'quantity_{self.tshirt.pk}'].initial, 0)
        self.assertEqual(form.fields[f'quantity_{self.jeans.pk}'].initial, 0)

    def test_buy_page_preselects_product(self):
        response = self.client.get(reverse('buy', args=[self.jeans.pk]))
        form = response.context['form']
        self.assertEqual(form.fields[f'quantity_{self.jeans.pk}'].initial, 1)
        self.assertEqual(form.fields[f'quantity_{self.tshirt.pk}'].initial, 0)

    def test_buy_unknown_product_returns_404(self):
        response = self.client.get(reverse('buy', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_post_to_unknown_product_returns_404(self):
        response = self.post_order(reverse('buy', args=[9999]),
                                   items=[(self.tshirt, 1)])
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_order_single_product_without_discount(self):
        response = self.post_order(items=[(self.jeans, 2)])
        self.assertTemplateUsed(response, 'shop/purchase_done.html')
        self.assertNotContains(response, 'Скидка')
        self.assertContains(response, 'Итого к оплате: 7000')
        self.assertEqual(Purchase.objects.get().discount, Decimal('0'))

    def test_order_with_discount_shows_breakdown(self):
        response = self.post_order(items=[(self.tshirt, 2), (self.jeans, 1)])
        self.assertContains(response, 'Сумма: 5900')
        self.assertContains(response,
                            'Скидка за покупку товаров разного вида: 590.00')
        self.assertContains(response, 'Итого к оплате: 5310.00')
        self.assertEqual(response.context['purchase'],
                         Purchase.objects.get())

    def test_order_via_buy_url(self):
        response = self.post_order(reverse('buy', args=[self.tshirt.pk]),
                                   items=[(self.tshirt, 1), (self.jeans, 1)])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Purchase.objects.get().total, Decimal('4230.00'))

    def test_empty_order_shows_error(self):
        response = self.post_order(items=[(self.tshirt, 0)])
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/purchase_form.html')
        self.assertContains(response, 'Выберите хотя бы один товар')
        self.assertEqual(Purchase.objects.count(), 0)

    def test_invalid_quantity_shows_error(self):
        response = self.post_order(items=[(self.tshirt, -3)])
        self.assertTemplateUsed(response, 'shop/purchase_form.html')
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_missing_person_shows_error(self):
        response = self.client.post(reverse('order'), {
            'address': 'ул. Мира', f'quantity_{self.tshirt.pk}': 1})
        self.assertIn('person', response.context['form'].errors)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_get_request_does_not_create_purchase(self):
        self.client.get(reverse('order'))
        self.assertEqual(Purchase.objects.count(), 0)
