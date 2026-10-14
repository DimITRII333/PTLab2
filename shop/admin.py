from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html

from .models import Product, Purchase, PurchaseItem

admin.site.site_header = 'Магазин одежды — администрирование'
admin.site.site_title = 'Магазин одежды'
admin.site.index_title = 'Управление магазином'

LOW_STOCK = 5


class StockFilter(admin.SimpleListFilter):
    """Фильтр товаров в правой панели по остатку на складе."""
    title = 'наличие на складе'
    parameter_name = 'stock'

    def lookups(self, request, model_admin):
        return [
            ('in', 'В наличии'),
            ('low', f'Заканчивается (≤ {LOW_STOCK} шт.)'),
            ('out', 'Нет в наличии'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'in':
            return queryset.filter(stock__gt=0)
        if self.value() == 'low':
            return queryset.filter(stock__gt=0, stock__lte=LOW_STOCK)
        if self.value() == 'out':
            return queryset.filter(stock=0)
        return queryset


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'stock_status')
    list_editable = ('price', 'stock')
    list_filter = (StockFilter,)
    search_fields = ('name',)
    ordering = ('name',)
    actions = ['add_ten_to_stock']

    @admin.display(description='Статус', ordering='stock')
    def stock_status(self, product):
        if product.stock == 0:
            color, text = 'gray', 'Нет в наличии'
        elif product.stock <= LOW_STOCK:
            color, text = 'darkorange', 'Заканчивается'
        else:
            color, text = 'green', 'В наличии'
        return format_html('<b style="color: {}">{}</b>', color, text)

    @admin.action(description='Пополнить склад на 10 шт.')
    def add_ten_to_stock(self, request, queryset):
        updated = queryset.update(stock=F('stock') + 10)
        self.message_user(request, f'Склад пополнен для товаров: {updated}')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('pk', 'person', 'date', 'subtotal', 'discount', 'total')
    list_filter = ('date',)
    search_fields = ('person', 'address')
    inlines = [PurchaseItemInline]
