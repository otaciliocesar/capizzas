from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def calc_total(carrinho):
    total = Decimal("0.00")
    for item in carrinho:
        total += Decimal(item.get('total', '0.00'))
    return "%.2f" % total
