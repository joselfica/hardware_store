"""
==============================================================================
MÓDULO DE MODELOS - GESTIÓN DE USUARIOS
==============================================================================
Este módulo define el modelo de usuario personalizado del sistema, extendiendo
AbstractUser de Django para incorporar atributos específicos del dominio de
negocio (rol, RUT, teléfono) y mantener la compatibilidad con el sistema de
autenticación nativo.

Diseño normalizado (3FN):
    - Los atributos son atómicos (1FN).
    - Todos dependen exclusivamente de la PK (2FN).
    - No existen dependencias transitivas: role se almacena como CHOICES
      directamente ligado al usuario, sin tabla intermedia porque es un
      atributo propio del usuario, no de una entidad externa (3FN).

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Modelo de Usuario personalizado del sistema.

    Hereda de AbstractUser para conservar toda la funcionalidad nativa
    (autenticación, permisos, grupos, hashing de contraseña, etc.) y añade
    atributos propios del negocio retail de hardware.

    Atributos heredados relevantes:
        - username, email, password, first_name, last_name
        - is_active, is_staff, is_superuser, date_joined

    Atributos personalizados:
        - role: diferencia entre Cliente y Administrador de TI (RBAC)
        - rut: identificador tributario chileno (opcional)
        - phone: teléfono de contacto (opcional)
    """

    # ------------------------------------------------------------------
    # CHOICES: Definición del catálogo controlado de roles del sistema.
    # Se implementa como clase anidada (TextChoices) siguiendo el patrón
    # recomendado por Django 3.0+ para agrupar constantes del modelo.
    # ------------------------------------------------------------------
    class Role(models.TextChoices):
        """
        Enumeración de roles disponibles para control de acceso basado en
        roles (RBAC). El valor almacenado en la BD es el primer elemento;
        el segundo es la etiqueta legible mostrada en formularios.
        """
        CLIENTE = 'CLIENTE', _('Cliente')
        ADMIN = 'ADMIN', _('Administrador de TI')

    # ------------------------------------------------------------------
    # ATRIBUTO: role
    # Determina los permisos del usuario en el sistema.
    # Es un campo de elección controlada (CHOICES) que por defecto asigna
    # el rol menos privilegiado (CLIENTE), aplicando el principio de
    # mínimo privilegio.
    # ------------------------------------------------------------------
    role = models.CharField(
        _('Rol del usuario'),
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENTE,
        db_index=True,  # Índice para acelerar filtros por rol
        help_text=_(
            'Define los permisos del usuario. '
            'CLIENTE: compra y gestiona su carro. '
            'ADMIN: gestiona catálogo, inventario y estados de órdenes.'
        ),
    )

    # ------------------------------------------------------------------
    # ATRIBUTO: rut
    # Identificador tributario chileno. Se valida con una expresión regular
    # que acepta formatos como "12.345.678-9" o "12345678-9".
    # Es opcional porque no todos los clientes lo proporcionan al registrarse.
    # ------------------------------------------------------------------
    rut = models.CharField(
        _('RUT'),
        max_length=12,
        blank=True,
        null=True,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]$',
                message=_('El RUT debe tener un formato válido (ej: 12.345.678-9).'),
            )
        ],
        help_text=_('RUT del usuario (formato 12.345.678-9).'),
    )

    # ------------------------------------------------------------------
    # ATRIBUTO: phone
    # Teléfono de contacto. Formato flexible para aceptar números chilenos
    # con o sin prefijo +56.
    # ------------------------------------------------------------------
    phone = models.CharField(
        _('Teléfono'),
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?56?9?\d{8}$|^\+?56?\d{9}$',
                message=_('Ingrese un teléfono chileno válido (ej: +56912345678).'),
            )
        ],
        help_text=_('Teléfono de contacto (ej: +56912345678).'),
    )

    # ------------------------------------------------------------------
    # METADATA del modelo
    # ------------------------------------------------------------------
    class Meta:
        db_table = 'users_user'                        # Nombre explícito en BD
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-date_joined']                    # Orden por defecto
        indexes = [
            models.Index(fields=['role']),             # Índice para filtros
            models.Index(fields=['email']),            # Índice para búsquedas
            models.Index(fields=['is_active']),
        ]

    # ------------------------------------------------------------------
    # MÉTODOS Y PROPIEDADES
    # ------------------------------------------------------------------
    def __str__(self):
        """Representación legible del usuario."""
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin_role(self):
        """
        Indica si el usuario posee el rol de Administrador de TI.
        Se utiliza en permisos DRF personalizados y en plantillas del frontend.

        Returns:
            bool: True si el rol es ADMIN, False en caso contrario.
        """
        return self.role == self.Role.ADMIN

    @property
    def full_name(self):
        """Retorna el nombre completo del usuario o su username como fallback."""
        return self.get_full_name() or self.username