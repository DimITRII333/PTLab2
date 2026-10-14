from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import FormView

from .form import PurchaseForm
from .models import Product
from .services import (DISCOUNT_PERCENT, MIN_DISTINCT_PRODUCTS,
                       OutOfStockError)


def index(request):
    products = Product.objects.order_by('pk')
    context = {
        'products': products,
        'discount_percent': DISCOUNT_PERCENT,
        'min_distinct_products': MIN_DISTINCT_PRODUCTS,
    }
    return render(request, 'shop/index.html', context)


class PurchaseCreate(FormView):
    form_class = PurchaseForm
    template_name = 'shop/purchase_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product_id = self.kwargs.get('product_id')
        if product_id is not None:
            kwargs['initial_product_id'] = get_object_or_404(
                Product, pk=product_id).pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discount_percent'] = DISCOUNT_PERCENT
        context['min_distinct_products'] = MIN_DISTINCT_PRODUCTS
        return context

    def form_valid(self, form):
        try:
            purchase = form.save()
        except OutOfStockError as error:
            # остаток успели выкупить, пока покупатель заполнял форму
            form.add_error(None, str(error))
            return self.form_invalid(form)
        return render(self.request, 'shop/purchase_done.html',
                      {'purchase': purchase})
