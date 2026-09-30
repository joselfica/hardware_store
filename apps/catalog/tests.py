"""
==============================================================================
TESTS DEL CATÁLOGO
==============================================================================
Tests unitarios e integrales para la app 'catalog'.

Actualmente sin tests implementados. Como trabajo futuro se podrían
agregar los siguientes casos:

Filtros:
    - test_filter_products_by_category()
    - test_filter_products_by_price_range()
    - test_filter_products_by_brand_name()
    - test_search_products_multiple_fields()

Serializers:
    - test_category_name_unique_case_insensitive()
    - test_product_sku_unique_uppercase()
    - test_product_price_must_be_positive()

ViewSets:
    - test_public_can_list_products()
    - test_client_cannot_create_product()  # 403
    - test_admin_can_create_product()      # 201
    - test_out_of_stock_products_hidden_from_public()

Framework sugerido: pytest-django o unittest de Django.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.test import TestCase

# Create your tests here.