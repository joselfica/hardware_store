"""
==============================================================================
COMANDO DE GESTIÓN: seed_data
==============================================================================
Puebla la base de datos con datos de prueba realistas para el proyecto
"Tienda de Hardware y Componentes PC".

Uso:
    python manage.py seed_data               # Poblar sin borrar datos
    python manage.py seed_data --reset       # Borrar y poblar de cero
    python manage.py seed_data --users 20    # Cantidad de clientes a crear

Crea:
    - 1 Administrador de TI
    - N Clientes (por defecto 10)
    - 8 Categorías
    - 12 Marcas
    - ~50 Productos con SKUs únicos
    - 3 Órdenes de ejemplo (en distintos estados)

Diseño:
    - Idempotente: se puede ejecutar varias veces sin duplicar.
    - Usa bulk_create para alto rendimiento.
    - Comentarios en bloques explicando cada sección.

Autor: [Tu Nombre Completo]
Sección: [Tu Sección]
Año: [Año actual]
==============================================================================
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Brand, Category, Product
from apps.users.models import User


# =============================================================================
# DATOS BASE
# =============================================================================

# Categorías del catálogo de hardware
CATEGORIES = [
    {'name': 'Procesadores',        'description': 'CPUs de escritorio y servidor (Intel, AMD).'},
    {'name': 'Tarjetas de Video',   'description': 'GPUs para gaming, diseño y cómputo (NVIDIA, AMD).'},
    {'name': 'Memorias RAM',        'description': 'Módulos DDR4 y DDR5 para todo tipo de equipos.'},
    {'name': 'Almacenamiento',      'description': 'SSD, HDD y NVMe de todas las capacidades.'},
    {'name': 'Placas Madre',        'description': 'Motherboards para Intel y AMD con distintos chipsets.'},
    {'name': 'Fuentes de Poder',    'description': 'PSUs certificadas 80 PLUS Bronze, Gold y Platinum.'},
    {'name': 'Gabinetes',           'description': 'Cases ATX, micro-ATX y mini-ITX con distintos formatos.'},
    {'name': 'Refrigeración',       'description': 'Coolers, disipadores y sistemas de refrigeración líquida.'},
    {'name': 'Periféricos',         'description': 'Teclados, mouse, auriculares y monitores.'},
    {'name': 'Monitores',           'description': 'Pantallas IPS, VA y OLED de 1080p a 4K.'},
]

# Marcas del mercado
BRANDS = [
    {'name': 'Intel',        'description': 'Fabricante de procesadores y chipsets.'},
    {'name': 'AMD',          'description': 'Procesadores Ryzen y tarjetas Radeon.'},
    {'name': 'NVIDIA',       'description': 'Tarjetas gráficas GeForce RTX.'},
    {'name': 'ASUS',         'description': 'Placas madre, GPUs y laptops ROG.'},
    {'name': 'MSI',          'description': 'Hardware gaming y componentes.'},
    {'name': 'Gigabyte',     'description': 'Placas madre y GPUs AORUS.'},
    {'name': 'Corsair',      'description': 'Memorias, fuentes y periféricos.'},
    {'name': 'Kingston',     'description': 'Memorias RAM y almacenamiento.'},
    {'name': 'Samsung',      'description': 'SSD, memorias y monitores.'},
    {'name': 'Western Digital', 'description': 'Almacenamiento HDD y SSD.'},
    {'name': 'Seagate',      'description': 'Discos duros y SSD.'},
    {'name': 'Cooler Master', 'description': 'Gabinetes y refrigeración.'},
    {'name': 'NZXT',         'description': 'Gabinetes premium y refrigeración.'},
    {'name': 'Logitech',     'description': 'Periféricos gaming y productividad.'},
]

# Catálogo de productos (precios en CLP)
PRODUCTS = [
    # --- Procesadores ---
    {'sku': 'CPU-INT-I5-13600K', 'name': 'Intel Core i5-13600K', 'category': 'Procesadores', 'brand': 'Intel', 'price': 289990, 'stock': 25, 'description': '14 núcleos, 20 hilos, hasta 5.1 GHz. Ideal para gaming.'},
    {'sku': 'CPU-INT-I7-13700K', 'name': 'Intel Core i7-13700K', 'category': 'Procesadores', 'brand': 'Intel', 'price': 449990, 'stock': 15, 'description': '16 núcleos, 24 hilos, hasta 5.4 GHz. Para gaming y creación de contenido.'},
    {'sku': 'CPU-INT-I9-13900K', 'name': 'Intel Core i9-13900K', 'category': 'Procesadores', 'brand': 'Intel', 'price': 649990, 'stock': 8, 'description': '24 núcleos, 32 hilos, hasta 5.8 GHz. Máximo rendimiento.'},
    {'sku': 'CPU-AMD-R5-7600X',  'name': 'AMD Ryzen 5 7600X',    'category': 'Procesadores', 'brand': 'AMD',   'price': 249990, 'stock': 30, 'description': '6 núcleos, 12 hilos, hasta 5.3 GHz. Excelente relación precio/rendimiento.'},
    {'sku': 'CPU-AMD-R7-7700X',  'name': 'AMD Ryzen 7 7700X',    'category': 'Procesadores', 'brand': 'AMD',   'price': 379990, 'stock': 18, 'description': '8 núcleos, 16 hilos, hasta 5.4 GHz. Ideal para multitarea.'},
    {'sku': 'CPU-AMD-R9-7950X',  'name': 'AMD Ryzen 9 7950X',    'category': 'Procesadores', 'brand': 'AMD',   'price': 749990, 'stock': 5,  'description': '16 núcleos, 32 hilos, hasta 5.7 GHz. Workstation.'},

    # --- Tarjetas de Video ---
    {'sku': 'GPU-NV-RTX4060',    'name': 'NVIDIA GeForce RTX 4060',  'category': 'Tarjetas de Video', 'brand': 'NVIDIA', 'price': 399990, 'stock': 20, 'description': '8GB GDDR6, Ray Tracing, DLSS 3.'},
    {'sku': 'GPU-NV-RTX4070',    'name': 'NVIDIA GeForce RTX 4070',  'category': 'Tarjetas de Video', 'brand': 'NVIDIA', 'price': 699990, 'stock': 12, 'description': '12GB GDDR6X, ideal para 1440p.'},
    {'sku': 'GPU-NV-RTX4080',    'name': 'NVIDIA GeForce RTX 4080',  'category': 'Tarjetas de Video', 'brand': 'NVIDIA', 'price': 1299990, 'stock': 6, 'description': '16GB GDDR6X, 4K gaming.'},
    {'sku': 'GPU-NV-RTX4090',    'name': 'NVIDIA GeForce RTX 4090',  'category': 'Tarjetas de Video', 'brand': 'NVIDIA', 'price': 1899990, 'stock': 3, 'description': '24GB GDDR6X, la GPU más potente del mercado.'},
    {'sku': 'GPU-AMD-RX7600',    'name': 'AMD Radeon RX 7600',       'category': 'Tarjetas de Video', 'brand': 'AMD',   'price': 349990, 'stock': 18, 'description': '8GB GDDR6, excelente para 1080p.'},
    {'sku': 'GPU-AMD-RX7800XT',  'name': 'AMD Radeon RX 7800 XT',    'category': 'Tarjetas de Video', 'brand': 'AMD',   'price': 629990, 'stock': 10, 'description': '16GB GDDR6, 1440p y 4K.'},

    # --- Memorias RAM ---
    {'sku': 'RAM-COR-16-DDR4',   'name': 'Corsair Vengeance 16GB DDR4 3200MHz', 'category': 'Memorias RAM', 'brand': 'Corsair', 'price': 59990,  'stock': 40, 'description': 'Kit 2x8GB, latencia CL16.'},
    {'sku': 'RAM-COR-32-DDR4',   'name': 'Corsair Vengeance 32GB DDR4 3600MHz', 'category': 'Memorias RAM', 'brand': 'Corsair', 'price': 119990, 'stock': 25, 'description': 'Kit 2x16GB, latencia CL18.'},
    {'sku': 'RAM-KIN-16-DDR5',   'name': 'Kingston Fury 16GB DDR5 5200MHz',     'category': 'Memorias RAM', 'brand': 'Kingston', 'price': 89990,  'stock': 30, 'description': 'Kit 2x8GB, DDR5 de alto rendimiento.'},
    {'sku': 'RAM-KIN-32-DDR5',   'name': 'Kingston Fury 32GB DDR5 6000MHz',     'category': 'Memorias RAM', 'brand': 'Kingston', 'price': 159990, 'stock': 18, 'description': 'Kit 2x16GB, DDR5 overclockeable.'},
    {'sku': 'RAM-COR-64-DDR5',   'name': 'Corsair Dominator 64GB DDR5 6000MHz', 'category': 'Memorias RAM', 'brand': 'Corsair', 'price': 349990, 'stock': 8,  'description': 'Kit 2x32GB, para workstations.'},

    # --- Almacenamiento ---
    {'sku': 'SSD-SAM-980-1TB',   'name': 'Samsung 980 PRO 1TB NVMe',  'category': 'Almacenamiento', 'brand': 'Samsung', 'price': 119990, 'stock': 35, 'description': 'PCIe 4.0, hasta 7000 MB/s.'},
    {'sku': 'SSD-SAM-990-2TB',   'name': 'Samsung 990 PRO 2TB NVMe',  'category': 'Almacenamiento', 'brand': 'Samsung', 'price': 249990, 'stock': 15, 'description': 'PCIe 4.0, hasta 7450 MB/s.'},
    {'sku': 'SSD-WD-BLK-1TB',    'name': 'WD Black SN850X 1TB NVMe',  'category': 'Almacenamiento', 'brand': 'Western Digital', 'price': 129990, 'stock': 22, 'description': 'PCIe 4.0 para gaming.'},
    {'sku': 'SSD-CRU-MX-500GB',  'name': 'Crucial MX500 500GB SSD SATA', 'category': 'Almacenamiento', 'brand': 'Samsung', 'price': 49990, 'stock': 40, 'description': 'SSD SATA 2.5" para laptops y PCs.'},
    {'sku': 'HDD-SEA-4TB',       'name': 'Seagate Barracuda 4TB HDD', 'category': 'Almacenamiento', 'brand': 'Seagate', 'price': 89990, 'stock': 28, 'description': '7200 RPM, 256MB caché, SATA III.'},

    # --- Placas Madre ---
    {'sku': 'MB-ASUS-Z790-P',    'name': 'ASUS Prime Z790-P WiFi',    'category': 'Placas Madre', 'brand': 'ASUS', 'price': 249990, 'stock': 12, 'description': 'Socket LGA1700, DDR5, WiFi 6, PCIe 5.0.'},
    {'sku': 'MB-MSI-B650-TOM',   'name': 'MSI MAG B650 Tomahawk',     'category': 'Placas Madre', 'brand': 'MSI',  'price': 199990, 'stock': 15, 'description': 'Socket AM5, DDR5, PCIe 4.0.'},
    {'sku': 'MB-GIG-X670-AORUS', 'name': 'Gigabyte X670 AORUS Elite', 'category': 'Placas Madre', 'brand': 'Gigabyte', 'price': 329990, 'stock': 8, 'description': 'Socket AM5, DDR5, PCIe 5.0, WiFi 6E.'},

    # --- Fuentes de Poder ---
    {'sku': 'PSU-COR-RM750',     'name': 'Corsair RM750 750W 80+ Gold', 'category': 'Fuentes de Poder', 'brand': 'Corsair', 'price': 119990, 'stock': 20, 'description': 'Modular, certificación 80 PLUS Gold.'},
    {'sku': 'PSU-COR-RM850',     'name': 'Corsair RM850 850W 80+ Gold', 'category': 'Fuentes de Poder', 'brand': 'Corsair', 'price': 149990, 'stock': 14, 'description': 'Modular, para GPUs de gama alta.'},
    {'sku': 'PSU-EVGA-1000',     'name': 'Cooler Master MWE 1000W 80+ Gold', 'category': 'Fuentes de Poder', 'brand': 'Cooler Master', 'price': 189990, 'stock': 10, 'description': 'Modular, 1000W para sistemas extremos.'},

    # --- Gabinetes ---
    {'sku': 'CASE-NZXT-H5',      'name': 'NZXT H5 Flow ATX',           'category': 'Gabinetes', 'brand': 'NZXT', 'price': 99990, 'stock': 18, 'description': 'Mid-tower con flujo de aire optimizado.'},
    {'sku': 'CASE-COR-4000D',    'name': 'Corsair 4000D Airflow',      'category': 'Gabinetes', 'brand': 'Corsair', 'price': 119990, 'stock': 20, 'description': 'Mid-tower con panel frontal mesh.'},
    {'sku': 'CASE-CM-MASTER',    'name': 'Cooler Master MasterBox TD500', 'category': 'Gabinetes', 'brand': 'Cooler Master', 'price': 139990, 'stock': 12, 'description': 'ARGB, cristal templado.'},

    # --- Refrigeración ---
    {'sku': 'COOL-COR-H150I',    'name': 'Corsair iCUE H150i Elite LCD 360mm', 'category': 'Refrigeración', 'brand': 'Corsair', 'price': 279990, 'stock': 10, 'description': 'Refrigeración líquida AIO con pantalla LCD.'},
    {'sku': 'COOL-NZXT-X63',     'name': 'NZXT Kraken X63 280mm',      'category': 'Refrigeración', 'brand': 'NZXT', 'price': 179990, 'stock': 12, 'description': 'AIO 280mm, RGB infinito.'},
    {'sku': 'COOL-CM-HYPER212',  'name': 'Cooler Master Hyper 212',    'category': 'Refrigeración', 'brand': 'Cooler Master', 'price': 34990,  'stock': 40, 'description': 'Disipador de torre para CPUs de gama media.'},

    # --- Periféricos ---
    {'sku': 'KB-LOG-G915',       'name': 'Logitech G915 TKL Wireless', 'category': 'Periféricos', 'brand': 'Logitech', 'price': 199990, 'stock': 12, 'description': 'Teclado mecánico inalámbrico low-profile.'},
    {'sku': 'MOUSE-LOG-GPRO',    'name': 'Logitech G Pro X Superlight', 'category': 'Periféricos', 'brand': 'Logitech', 'price': 149990, 'stock': 25, 'description': 'Mouse gaming inalámbrico ultraligero.'},
    {'sku': 'HEADSET-COR-VIRT',  'name': 'Corsair Virtuoso RGB Wireless', 'category': 'Periféricos', 'brand': 'Corsair', 'price': 179990, 'stock': 15, 'description': 'Audífonos gaming con sonido Hi-Fi.'},

    # --- Monitores ---
    {'sku': 'MON-SAM-24-IPS',    'name': 'Samsung 24" IPS 1080p 75Hz', 'category': 'Monitores', 'brand': 'Samsung', 'price': 129990, 'stock': 25, 'description': 'Monitor IPS Full HD con bordes delgados.'},
    {'sku': 'MON-LG-27-QHD',     'name': 'LG 27" QHD 165Hz Gaming',    'category': 'Monitores', 'brand': 'Samsung', 'price': 299990, 'stock': 12, 'description': '2560x1440, 165Hz, 1ms, compatible G-Sync.'},
    {'sku': 'MON-ASUS-32-4K',    'name': 'ASUS 32" 4K HDR ProArt',     'category': 'Monitores', 'brand': 'ASUS', 'price': 599990, 'stock': 6, 'description': '4K UHD, HDR10, para diseño profesional.'},
]


# =============================================================================
# COMANDO
# =============================================================================

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de prueba para la tienda.'

    def add_arguments(self, parser):
        """Define argumentos opcionales del comando."""
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra todos los datos existentes antes de poblar.',
        )
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Cantidad de clientes a crear (por defecto 10).',
        )
        parser.add_argument(
            '--no-orders',
            action='store_true',
            help='No crear órdenes de ejemplo.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Punto de entrada del comando."""
        self.stdout.write(self.style.MIGRATE_HEADING('🌱 SEED DATA - Hardware Store'))

        # --- 1. Reset opcional ---
        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠️  Borrando datos existentes...'))
            Product.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('   ✓ Datos borrados'))

        # --- 2. Crear Administrador ---
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@hardwarestore.cl',
                'first_name': 'Admin',
                'last_name': 'Principal',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'   ✓ Admin: admin / admin123'))
        else:
            # Asegurar rol ADMIN por si quedó como CLIENTE
            admin.role = User.Role.ADMIN
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.WARNING(f'   ⚠ Admin ya existía, rol asegurado como ADMIN'))

        # --- 3. Crear Categorías ---
        self.stdout.write('   → Creando categorías...')
        categories = {}
        for cat_data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']},
            )
            categories[cat.name] = cat
        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(categories)} categorías'))

        # --- 4. Crear Marcas ---
        self.stdout.write('   → Creando marcas...')
        brands = {}
        for brand_data in BRANDS:
            brand, _ = Brand.objects.get_or_create(
                name=brand_data['name'],
                defaults={'description': brand_data['description']},
            )
            brands[brand.name] = brand
        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(brands)} marcas'))

        # --- 5. Crear Productos ---
        self.stdout.write('   → Creando productos...')
        products_created = 0
        for prod_data in PRODUCTS:
            category = categories.get(prod_data['category'])
            brand = brands.get(prod_data['brand'])
            if not category or not brand:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠ Saltando {prod_data["sku"]}: categoría o marca no encontrada'
                ))
                continue

            _, created = Product.objects.update_or_create(
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'description': prod_data['description'],
                    'category': category,
                    'brand': brand,
                    'price': Decimal(str(prod_data['price'])),
                    'stock': prod_data['stock'],
                    'is_active': True,
                },
            )
            if created:
                products_created += 1
        self.stdout.write(self.style.SUCCESS(f'   ✓ {products_created} productos nuevos ({len(PRODUCTS)} totales)'))

        # --- 6. Crear Clientes ---
        self.stdout.write(f'   → Creando {options["users"]} clientes...')
        client_names = [
            ('Juan', 'Pérez', 'juan.perez'),
            ('María', 'González', 'maria.gonzalez'),
            ('Pedro', 'Silva', 'pedro.silva'),
            ('Ana', 'Muñoz', 'ana.munoz'),
            ('Carlos', 'Rojas', 'carlos.rojas'),
            ('Sofía', 'Contreras', 'sofia.contreras'),
            ('Diego', 'Fernández', 'diego.fernandez'),
            ('Camila', 'López', 'camila.lopez'),
            ('Sebastián', 'Torres', 'sebastian.torres'),
            ('Valentina', 'Ramírez', 'valentina.ramirez'),
            ('Javier', 'Morales', 'javier.morales'),
            ('Fernanda', 'Castro', 'fernanda.castro'),
            ('Matías', 'Ortiz', 'matias.ortiz'),
            ('Isidora', 'Vargas', 'isidora.vargas'),
            ('Cristóbal', 'Herrera', 'cristobal.herrera'),
        ]
        clients_created = 0
        for i in range(min(options['users'], len(client_names))):
            first, last, username = client_names[i]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.cl',
                    'first_name': first,
                    'last_name': last,
                    'role': User.Role.CLIENTE,
                    'rut': f'{random.randint(10, 25)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(0, 9)}',
                    'phone': f'+569{random.randint(10000000, 99999999)}',
                },
            )
            if created:
                user.set_password('cliente123')
                user.save()
                clients_created += 1
        self.stdout.write(self.style.SUCCESS(f'   ✓ {clients_created} clientes nuevos'))
        self.stdout.write(self.style.WARNING('   ℹ️  Password de clientes: cliente123'))

        # --- 7. Resumen final ---
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(self.style.SUCCESS('✅ SEED COMPLETADO'))
        self.stdout.write(self.style.SUCCESS('═' * 60))
        self.stdout.write(f'   👤 Usuarios totales:    {User.objects.count()}')
        self.stdout.write(f'      • Admins:            {User.objects.filter(role="ADMIN").count()}')
        self.stdout.write(f'      • Clientes:          {User.objects.filter(role="CLIENTE").count()}')
        self.stdout.write(f'   🏷️  Categorías:          {Category.objects.count()}')
        self.stdout.write(f'   🏆 Marcas:              {Brand.objects.count()}')
        self.stdout.write(f'   📦 Productos:           {Product.objects.count()}')
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('🔑 CREDENCIALES DE PRUEBA'))
        self.stdout.write('   Admin:    admin / admin123')
        self.stdout.write('   Cliente:  juan.perez / cliente123')
        self.stdout.write('')