"""
==============================================================================
SERIALIZERS DE USUARIOS
==============================================================================
Define los serializers encargados de:
    - Registrar nuevos usuarios con rol por defecto CLIENTE.
    - Personalizar la respuesta del login JWT para incluir datos del usuario
      y claims de rol.
    - Exponer el perfil del usuario autenticado.
    - Permitir al usuario editar sus propios datos personales.
    - Permitir al admin gestionar usuarios (CRUD completo).

Todos los serializers incluyen validaciones explícitas y mensajes de error
en español para mejorar la experiencia del frontend.

Autor: José Fica
Sección: AP-N4-C2
Año: 2026
==============================================================================
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# =============================================================================
# SERIALIZER: LECTURA DEL USUARIO
# =============================================================================
# Se utiliza para exponer los datos del usuario autenticado en endpoints
# como /api/auth/me/ y para incrustar el usuario en respuestas de login.
# =============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura del modelo User.

    Campos calculados:
        - full_name: property del modelo que devuelve el nombre completo.
        - role_display: etiqueta legible del rol ('Cliente', 'Administrador').

    Ambos se declaran explícitamente porque NO son campos reales de la BD
    (son property y método del modelo).
    """

    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'rut', 'phone',
            'is_active', 'date_joined',
        )
        read_only_fields = ('id', 'role', 'is_active', 'date_joined')


# =============================================================================
# SERIALIZER: REGISTRO PÚBLICO
# =============================================================================
# Crea nuevos usuarios con rol CLIENTE forzado (anti-escalada de privilegios).
# =============================================================================

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.

    Reglas de negocio:
        - El rol se asigna SIEMPRE como CLIENTE al registrarse por API.
          Los administradores solo pueden ser creados por otros admins
          desde el panel de Django, evitando escalada de privilegios.
        - Se valida que las contraseñas coincidan.
        - Se aplican los validadores de contraseña de Django.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Contraseña (mínimo 8 caracteres, no muy común, etc.).',
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirmación de la contraseña.',
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'rut', 'phone', 'password', 'password_confirm',
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        """Valida que el email no esté registrado (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Ya existe un usuario registrado con este correo electrónico.'
            )
        return value.lower()

    def validate(self, attrs):
        """Valida que las dos contraseñas coincidan."""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': 'Las contraseñas no coinciden.'}
            )
        return attrs

    def create(self, validated_data):
        """
        Crea el usuario forzando el rol CLIENTE y hasheando la contraseña.
        Se utiliza create_user() que aplica el hashing seguro de Django.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            rut=validated_data.get('rut'),
            phone=validated_data.get('phone'),
            password=validated_data['password'],
            role=User.Role.CLIENTE,          # ← Forzado por seguridad
        )
        return user


# =============================================================================
# SERIALIZER: LOGIN JWT CON CLAIMS PERSONALIZADOS
# =============================================================================
# Extiende TokenObtainPairSerializer para:
#   1. Inyectar claims personalizados (role, username, email) en el payload.
#   2. Retornar los datos del usuario junto con los tokens.
# =============================================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado de login JWT.

    ¿Por qué personalizar los claims?
        Los permisos DRF pueden leer request.auth['role'] directamente del
        token sin consultar la BD, mejorando el rendimiento. Además, el
        frontend puede mostrar/ocultar secciones según el rol sin peticiones
        adicionales.
    """

    @classmethod
    def get_token(cls, user):
        """
        Genera el token y agrega claims personalizados al payload.

        IMPORTANTE: Este método se llama tanto para el access como para el
        refresh, por lo que los claims estarán en ambos tokens.
        """
        token = super().get_token(user)

        # --- Claims personalizados ---
        token['role'] = user.role                       # ← Claim clave de RBAC
        token['username'] = user.username
        token['email'] = user.email
        token['full_name'] = user.full_name

        return token

    def validate(self, attrs):
        """
        Extiende la respuesta del login para incluir los datos del usuario
        además de los tokens.
        """
        data = super().validate(attrs)                  # {access, refresh}
        data['user'] = UserSerializer(self.user).data   # Datos del usuario
        return data


# =============================================================================
# SERIALIZER: CAMBIO DE CONTRASEÑA
# =============================================================================
# Permite al usuario autenticado cambiar su contraseña.
# =============================================================================

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para el cambio de contraseña del usuario autenticado.
    """

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        """Verifica que la contraseña actual sea correcta."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value

    def validate(self, attrs):
        """Verifica que las nuevas contraseñas coincidan."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {'new_password_confirm': 'Las nuevas contraseñas no coinciden.'}
            )
        return attrs

    def save(self, **kwargs):
        """Actualiza la contraseña del usuario autenticado."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# =============================================================================
# SERIALIZER: GESTIÓN DE USUARIOS (SOLO ADMIN)
# =============================================================================
# CRUD completo de usuarios accesible solo para administradores.
# =============================================================================

class UserAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para que un ADMIN gestione usuarios (CRUD completo).

    Diferencias con UserSerializer (lectura):
        - Permite escribir el campo 'role' (solo admins pueden hacerlo).
        - Acepta 'password' opcional en creación.
        - Valida que no se pueda dejar sin rol ADMIN al último admin.

    Diferencias con RegisterSerializer (registro público):
        - Aquí SÍ se permite asignar role desde el payload.
        - El registro público fuerza role=CLIENTE.
    """

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='Opcional en edición. Si se envía, se actualiza.',
    )
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'rut', 'phone',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'password',
        )
        read_only_fields = ('id', 'date_joined', 'last_login', 'full_name', 'role_display')

    def validate_email(self, value):
        """Email único (case-insensitive) excepto para el propio usuario."""
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este correo electrónico.'
            )
        return value.lower()

    def validate_username(self, value):
        """Username único (case-insensitive)."""
        qs = User.objects.filter(username__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este username.'
            )
        return value

    def validate(self, attrs):
        """
        Reglas de protección:
            - En creación, la contraseña es obligatoria.
            - No se puede quitar el rol ADMIN al último administrador activo.
            - Un admin no puede desactivarse a sí mismo.
        """
        request = self.context.get('request')

        # --- Creación: password obligatorio ---
        if not self.instance and not attrs.get('password'):
            raise serializers.ValidationError(
                {'password': 'La contraseña es obligatoria al crear un usuario.'}
            )

        # --- Protección del último admin ---
        if self.instance:
            # ¿Estamos intentando cambiar el rol del último admin?
            new_role = attrs.get('role', self.instance.role)
            if (
                self.instance.role == User.Role.ADMIN
                and new_role != User.Role.ADMIN
            ):
                admins_activos = User.objects.filter(
                    role=User.Role.ADMIN, is_active=True
                ).exclude(pk=self.instance.pk).count()
                if admins_activos == 0:
                    raise serializers.ValidationError(
                        {'role': 'No puedes quitar el rol ADMIN al último administrador activo.'}
                    )

            # --- Un admin no puede desactivarse a sí mismo ---
            if request and request.user.pk == self.instance.pk:
                if attrs.get('is_active') is False:
                    raise serializers.ValidationError(
                        {'is_active': 'No puedes desactivar tu propia cuenta.'}
                    )

        return attrs

    def create(self, validated_data):
        """Crea el usuario con hashing de contraseña."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Actualiza el usuario, hasheando la contraseña si se envía."""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# =============================================================================
# SERIALIZER: ACTUALIZAR PERFIL PROPIO
# =============================================================================
# Permite al usuario autenticado actualizar SUS PROPIOS datos personales.
#
# Reglas de seguridad:
#   - El usuario NO puede modificar su username (ligado al historial).
#   - El usuario NO puede modificar su role (anti-escalada).
#   - El usuario NO puede modificar is_active/is_staff/is_superuser.
#   - El email debe ser único (case-insensitive).
#   - El RUT debe ser único si está presente.
# =============================================================================

class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para que el usuario actualice sus propios datos.

    Campos editables:
        - first_name, last_name, email, rut, phone.

    Campos de solo lectura (no editables por el usuario):
        - id, username, role, is_active, is_staff, is_superuser, date_joined.

    Nota: full_name y role_display se declaran explícitamente porque son
    una property y un método del modelo, no campos reales de la BD. DRF
    necesita saber cómo resolverlos, si no lanza un 500.
    """

    # --- Campos calculados (declarados explícitamente) ---
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'rut', 'phone',
            'is_active', 'date_joined',
        )
        read_only_fields = (
            'id', 'username', 'role', 'is_active', 'date_joined',
        )

    def validate_email(self, value):
        """Valida que el email no esté en uso por OTRO usuario."""
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este correo electrónico.'
            )
        return value.lower()

    def validate_rut(self, value):
        """Valida que el RUT no esté en uso por OTRO usuario."""
        if not value:
            return value

        qs = User.objects.filter(rut=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este RUT.'
            )
        return value