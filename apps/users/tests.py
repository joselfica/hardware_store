"""
==============================================================================
TESTS DE USUARIOS
==============================================================================
Tests unitarios e integrales para la app 'users'.

Actualmente sin tests implementados. Como trabajo futuro se podrían
agregar los siguientes casos:

Autenticación:
    - test_register_creates_user_with_client_role()
    - test_register_ignores_role_from_payload()
    - test_login_returns_tokens_with_role_claim()
    - test_logout_blacklists_refresh_token()
    - test_change_password_validates_old_password()

Permisos RBAC:
    - test_client_cannot_access_user_list()      # 403
    - test_admin_can_list_users()                # 200
    - test_admin_cannot_delete_self()            # 403
    - test_admin_cannot_delete_last_active_admin()  # 403

Soft delete:
    - test_delete_user_without_orders_is_hard_delete()  # 204
    - test_delete_user_with_orders_is_soft_delete()     # 200
    - test_soft_deleted_user_has_renamed_username()

Framework sugerido: pytest-django o unittest de Django.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.test import TestCase

# Create your tests here.