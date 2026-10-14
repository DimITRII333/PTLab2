from django import forms

from .models import Product, Purchase
from .services import create_purchase

MAX_QUANTITY = 100


class PurchaseForm(forms.ModelForm):
    """Форма оформления заказа: данные покупателя и количество
    каждого товара. Поля количества создаются динамически по каталогу."""

    class Meta:
        model = Purchase
        fields = ['person', 'address']
        labels = {
            'person': 'Введите свое имя',
            'address': 'Введите адрес доставки',
        }

    def __init__(self, *args, products=None, initial_product_id=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.products = list(products if products is not None
                             else Product.objects.order_by('pk'))
        for product in self.products:
            self.fields[self.quantity_field_name(product)] = \
                forms.IntegerField(
                    label=product.name,
                    min_value=0,
                    max_value=MAX_QUANTITY,
                    required=False,
                    initial=1 if (product.pk == initial_product_id
                                  and product.in_stock) else 0,
                )
        # Стили Bootstrap для всех полей формы
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    @staticmethod
    def quantity_field_name(product):
        return f'quantity_{product.pk}'

    def quantity_fields(self):
        """Пары (товар, поле количества) для вывода в шаблоне."""
        return [(product, self[self.quantity_field_name(product)])
                for product in self.products]

    def get_items(self):
        return [(product,
                 self.cleaned_data.get(self.quantity_field_name(product))
                 or 0)
                for product in self.products]

    def clean(self):
        cleaned_data = super().clean()
        items = self.get_items()
        if not any(quantity > 0 for _, quantity in items):
            raise forms.ValidationError(
                'Выберите хотя бы один товар для покупки.')
        for product, quantity in items:
            if quantity > product.stock:
                self.add_error(
                    self.quantity_field_name(product),
                    f'В наличии только {product.stock} шт.')
        return cleaned_data

    def save(self, commit=True):
        return create_purchase(self.cleaned_data['person'],
                               self.cleaned_data['address'],
                               self.get_items())
