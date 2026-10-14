from django.contrib import admin

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
    list_display = ('name', 'price', 'stock')
    list_filter = (StockFilter,)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'person', 'date', 'subtotal', 'discount', 'total')
    list_filter = ('date',)
    search_fields = ('person', 'address')
    inlines = [PurchaseItemInline]
