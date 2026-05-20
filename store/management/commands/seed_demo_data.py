# Author: Equipo Kibo
# Seeder de datos demo para Kibo

import random
from decimal import Decimal

import requests as http_client

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from accounts.models import UserProfile
from store.models import (
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Product,
    Review,
    Wishlist,
)


CATEGORIES = [
    {'name': 'Alimento',   'name_en': 'Food',        'description': 'Comida premium y balanceada para distintas etapas de vida.'},
    {'name': 'Juguetes',   'name_en': 'Toys',        'description': 'Juguetes para estimular y entretener a tu mascota.'},
    {'name': 'Higiene',    'name_en': 'Hygiene',     'description': 'Productos de limpieza, arenas y cuidado general.'},
    {'name': 'Accesorios', 'name_en': 'Accessories', 'description': 'Collares, correas, camas, comederos y más.'},
    {'name': 'Salud',      'name_en': 'Health',      'description': 'Suplementos y cuidados para bienestar diario.'},
]

# Campos: nombre, categoría, tipo_mascota, etapa_vida, precio, stock, img_seed, descripción
PRODUCTS = [
    # ── ALIMENTO ──────────────────────────────────────────────────────
    (
        'Concentrado Premium Cachorro',
        'Alimento', 'perro', 'cachorro', Decimal('89.90'), 45, 'dog-food-1',
        'Fórmula especial para cachorros con DHA, calcio y proteínas de alta digestibilidad. Apoya el desarrollo óseo y cerebral en los primeros 12 meses.',
    ),
    (
        'Concentrado Adulto Raza Pequeña',
        'Alimento', 'perro', 'adulto', Decimal('95.00'), 38, 'dog-food-2',
        'Croquetas de tamaño reducido para razas pequeñas. Alta energía, antioxidantes y ácidos grasos esenciales para mantener el peso ideal.',
    ),
    (
        'Alimento Húmedo Gato Pollo 12 latas',
        'Alimento', 'gato', 'adulto', Decimal('48.00'), 25, 'cat-food-1',
        'Pack de 12 latas de paté de pollo al natural. Sin conservantes artificiales, 80% de humedad para hidratación óptima del gato adulto.',
    ),
    (
        'Snack Dental Canino',
        'Alimento', 'perro', 'adulto', Decimal('18.90'), 80, 'dog-snack',
        'Masticables en forma de huesito que reducen el sarro y refrescan el aliento. Con menta natural y zinc quelado.',
    ),
    (
        'Croquetas Senior Gato',
        'Alimento', 'gato', 'senior', Decimal('76.30'), 29, 'cat-food-2',
        'Fórmula especial para gatos mayores de 7 años. Bajo en fósforo, con glucosamina para articulaciones y extra vitamina E.',
    ),
    (
        'Alimento Semillas Mixtas para Aves',
        'Alimento', 'ave', 'adulto', Decimal('22.00'), 55, 'bird-food',
        'Mezcla premium de mijo, cañamo, alpiste y girasol. Sin colorantes. Ideal para periquitos, canarios y agapornis.',
    ),

    # ── JUGUETES ──────────────────────────────────────────────────────
    (
        'Pelota Reforzada Mordible',
        'Juguetes', 'perro', 'todos', Decimal('22.00'), 60, 'dog-ball',
        'Pelota de caucho natural resistente a mordidas fuertes. Rebote impredecible que mantiene al perro activo y estimulado.',
    ),
    (
        'Ratón Interactivo con Catnip',
        'Juguetes', 'gato', 'todos', Decimal('15.50'), 74, 'cat-toy-1',
        'Ratón de peluche relleno con hierba gatera orgánica. El sonido interno y el catnip activan el instinto cazador del gato.',
    ),
    (
        'Cuerda Trenzada XL',
        'Juguetes', 'perro', 'adulto', Decimal('19.99'), 33, 'dog-rope',
        'Cuerda de algodón 100% natural, resistente al jaloneo. Limpia los dientes al masticar y ejercita la mandíbula.',
    ),
    (
        'Túnel Plegable para Gatos',
        'Juguetes', 'gato', 'adulto', Decimal('45.00'), 15, 'cat-tunnel',
        'Túnel de 90 cm con agujero central. Cruje al ser explorado, estimulando el instinto de caza. Plegable y fácil de guardar.',
    ),
    (
        'Disco Volador Flexible',
        'Juguetes', 'perro', 'adulto', Decimal('28.90'), 41, 'dog-frisbee',
        'Frisbee de silicona suave que no daña la boca. Flota en el agua, ideal para perros nadadores. Diámetro 25 cm.',
    ),
    (
        'Dispensador de Premios Inteligente',
        'Juguetes', 'perro', 'todos', Decimal('35.00'), 28, 'dog-puzzle',
        'Juguete tipo puzzle de nivel 2. El perro debe mover fichas para obtener el premio. Reduce ansiedad y estimula la mente.',
    ),

    # ── HIGIENE ───────────────────────────────────────────────────────
    (
        'Arena Aglomerante Lavanda 10kg',
        'Higiene', 'gato', 'todos', Decimal('55.00'), 27, 'cat-litter',
        'Arena de arcilla natural con esencia de lavanda. Aglomeración rápida, control de olores hasta 7 días. Bajo nivel de polvo.',
    ),
    (
        'Shampoo Hipoalergénico Canino',
        'Higiene', 'perro', 'todos', Decimal('34.90'), 50, 'dog-shampoo',
        'Shampoo con avena coloidal y aloe vera. Sin sulfatos ni parabenos. Ideal para pieles sensibles y pelajes opacos. 500 ml.',
    ),
    (
        'Toallitas Húmedas Mascotas x80',
        'Higiene', 'todos', 'todos', Decimal('21.00'), 66, 'pet-wipes',
        'Toallitas con extracto de manzanilla y pH neutro. Sin alcohol. Perfectas para limpiar patas, orejas y áreas sensibles.',
    ),
    (
        'Removedor de Olores Enzimático',
        'Higiene', 'todos', 'todos', Decimal('39.90'), 24, 'odor-remover',
        'Fórmula enzimática que elimina manchas y olores de orina, heces y vómito. Apto para telas, alfombras y pisos. 750 ml.',
    ),
    (
        'Cortauñas Profesional Mascotas',
        'Higiene', 'todos', 'todos', Decimal('28.50'), 35, 'nail-clipper',
        'Cortauñas de acero inoxidable con guarda de seguridad antideslizante. Para razas pequeñas y medianas. Filo duradero.',
    ),
    (
        'Cepillo Deslizador Pelo Largo',
        'Higiene', 'perro', 'adulto', Decimal('32.00'), 42, 'dog-brush',
        'Cepillo deslizador con púas de acero inoxidable. Elimina nudos, pelo muerto y suciedad sin irritar la piel. Agarre ergonómico.',
    ),

    # ── ACCESORIOS ────────────────────────────────────────────────────
    (
        'Cama Ortopédica Mediana',
        'Accesorios', 'perro', 'senior', Decimal('149.00'), 12, 'dog-bed',
        'Cama con espuma viscoelástica de 8 cm. Alivia presión en articulaciones para perros adultos y senior. Funda lavable. 70x55 cm.',
    ),
    (
        'Arnés Ajustable Reflectivo',
        'Accesorios', 'perro', 'adulto', Decimal('42.50'), 31, 'dog-harness',
        'Arnés de malla transpirable con tiras reflectivas 360°. No jala del cuello, distribuye la presión en el pecho. Talla M.',
    ),
    (
        'Rascador Torre Compacta',
        'Accesorios', 'gato', 'adulto', Decimal('129.90'), 9, 'cat-scratcher',
        'Torre de rascado de 80 cm con plataforma superior, casita y colgante. Sisal natural, base antideslizante. Gris marengo.',
    ),
    (
        'Comedero Antiansiedad',
        'Accesorios', 'perro', 'adulto', Decimal('37.80'), 44, 'slow-feeder',
        'Comedero con laberinto interno que obliga al perro a comer despacio. Reduce la ingesta de aire y previene el síndrome gástrico.',
    ),
    (
        'Placa de Identificación Personalizada',
        'Accesorios', 'todos', 'todos', Decimal('16.00'), 92, 'id-tag',
        'Placa de acero inoxidable grabada con nombre y teléfono. Disponible en formas: hueso, corazón, estrella. Resistente al agua.',
    ),
    (
        'Transportadora Aérea Talla M',
        'Accesorios', 'todos', 'todos', Decimal('89.00'), 17, 'pet-carrier',
        'Transportadora aprobada por aerolíneas. Malla ventilada, base rígida con colchoneta extraíble. Para mascotas hasta 7 kg.',
    ),

    # ── SALUD ─────────────────────────────────────────────────────────
    (
        'Omega 3 para Pelaje Brillante',
        'Salud', 'todos', 'adulto', Decimal('47.00'), 36, 'omega3',
        'Cápsulas de aceite de salmón rico en EPA y DHA. Mejora el brillo del pelaje, reduce la inflamación y apoya la función cardíaca.',
    ),
    (
        'Probiótico Digestivo Mascotas',
        'Salud', 'todos', 'adulto', Decimal('52.50'), 22, 'probiotic',
        'Mezcla de 7 cepas probióticas + prebióticos FOS. Regula la flora intestinal, reduce gases y mejora la consistencia de heces.',
    ),
    (
        'Suplemento Articular Senior',
        'Salud', 'perro', 'senior', Decimal('68.00'), 18, 'joint-supplement',
        'Glucosamina + condroitina + MSM en polvo. Reduce dolor articular en perros con artrosis. Sabor pollo. 60 porciones.',
    ),
    (
        'Vitaminas Multiespecie',
        'Salud', 'todos', 'todos', Decimal('40.00'), 30, 'vitamins',
        'Complejo vitamínico A, B, C, D y E más minerales quelados. En comprimidos masticables sabor hígado. 90 unidades.',
    ),
    (
        'Antiparasitario Externo Mensual',
        'Salud', 'todos', 'adulto', Decimal('35.00'), 50, 'antiparasitic',
        'Pipeta spot-on de acción mensual contra pulgas, garrapatas y mosquitos. Seguro desde los 2 meses de edad. Por dosis.',
    ),
    (
        'Crema Cicatrizante para Patas',
        'Salud', 'perro', 'todos', Decimal('28.90'), 55, 'paw-cream',
        'Crema con manteca de karité, vitamina E y árbol del té. Hidrata y cura fisuras en almohadillas. No tóxica si se lame.',
    ),
]

# Traducciones al inglés: {nombre_es: (name_en, description_en)}
TRANSLATIONS_EN = {
    'Concentrado Premium Cachorro': (
        'Premium Puppy Food',
        'Special formula for puppies with DHA, calcium and highly digestible proteins. Supports bone and brain development in the first 12 months.',
    ),
    'Concentrado Adulto Raza Pequeña': (
        'Adult Small Breed Food',
        'Small-sized kibble for small breeds. High energy, antioxidants and essential fatty acids to maintain ideal weight.',
    ),
    'Alimento Húmedo Gato Pollo 12 latas': (
        'Wet Cat Food Chicken 12 Cans',
        '12-can pack of natural chicken pâté. No artificial preservatives, 80% moisture for optimal adult cat hydration.',
    ),
    'Snack Dental Canino': (
        'Canine Dental Chew',
        'Bone-shaped chews that reduce tartar and freshen breath. With natural mint and chelated zinc.',
    ),
    'Croquetas Senior Gato': (
        'Senior Cat Kibble',
        'Special formula for cats over 7 years. Low phosphorus, with glucosamine for joints and extra vitamin E.',
    ),
    'Alimento Semillas Mixtas para Aves': (
        'Mixed Seed Bird Food',
        'Premium mix of millet, hemp, canary grass and sunflower seeds. No colorings. Ideal for parakeets, canaries and lovebirds.',
    ),
    'Pelota Reforzada Mordible': (
        'Reinforced Chew Ball',
        'Natural rubber ball resistant to strong bites. Unpredictable bounce that keeps the dog active and stimulated.',
    ),
    'Ratón Interactivo con Catnip': (
        'Interactive Mouse with Catnip',
        'Plush mouse filled with organic catnip. Internal sound and catnip activate the cat\'s hunting instinct.',
    ),
    'Cuerda Trenzada XL': (
        'XL Braided Rope',
        '100% natural cotton rope, resistant to tugging. Cleans teeth while chewing and exercises the jaw.',
    ),
    'Túnel Plegable para Gatos': (
        'Foldable Cat Tunnel',
        '90 cm tunnel with central hole. Crinkles when explored, stimulating hunting instinct. Foldable and easy to store.',
    ),
    'Disco Volador Flexible': (
        'Flexible Flying Disc',
        'Soft silicone frisbee that won\'t hurt the mouth. Floats on water, ideal for swimming dogs. 25 cm diameter.',
    ),
    'Dispensador de Premios Inteligente': (
        'Smart Treat Dispenser',
        'Level 2 puzzle toy. The dog must slide pieces to get the treat. Reduces anxiety and stimulates the mind.',
    ),
    'Arena Aglomerante Lavanda 10kg': (
        'Clumping Lavender Litter 10kg',
        'Natural clay litter with lavender scent. Fast clumping, odor control up to 7 days. Low dust level.',
    ),
    'Shampoo Hipoalergénico Canino': (
        'Canine Hypoallergenic Shampoo',
        'Shampoo with colloidal oatmeal and aloe vera. No sulfates or parabens. Ideal for sensitive skin and dull coats. 500 ml.',
    ),
    'Toallitas Húmedas Mascotas x80': (
        'Pet Wet Wipes x80',
        'Wipes with chamomile extract and neutral pH. Alcohol-free. Perfect for cleaning paws, ears and sensitive areas.',
    ),
    'Removedor de Olores Enzimático': (
        'Enzymatic Odor Remover',
        'Enzymatic formula that eliminates stains and odors from urine, feces and vomit. Safe for fabrics, carpets and floors. 750 ml.',
    ),
    'Cortauñas Profesional Mascotas': (
        'Professional Pet Nail Clipper',
        'Stainless steel nail clipper with non-slip safety guard. For small and medium breeds. Long-lasting sharpness.',
    ),
    'Cepillo Deslizador Pelo Largo': (
        'Long Hair Slicker Brush',
        'Slicker brush with stainless steel pins. Removes knots, dead hair and dirt without irritating the skin. Ergonomic grip.',
    ),
    'Cama Ortopédica Mediana': (
        'Medium Orthopedic Bed',
        'Bed with 8 cm memory foam. Relieves pressure on joints for adult and senior dogs. Washable cover. 70x55 cm.',
    ),
    'Arnés Ajustable Reflectivo': (
        'Reflective Adjustable Harness',
        'Breathable mesh harness with 360° reflective strips. No neck pulling, distributes pressure on chest. Size M.',
    ),
    'Rascador Torre Compacta': (
        'Compact Cat Tree Scratcher',
        '80 cm scratching tower with top platform, house and hanging toy. Natural sisal, non-slip base. Charcoal gray.',
    ),
    'Comedero Antiansiedad': (
        'Anti-Anxiety Slow Feeder',
        'Bowl with internal maze that forces the dog to eat slowly. Reduces air intake and prevents gastric syndrome.',
    ),
    'Placa de Identificación Personalizada': (
        'Custom ID Tag',
        'Engraved stainless steel tag with name and phone number. Available in shapes: bone, heart, star. Water resistant.',
    ),
    'Transportadora Aérea Talla M': (
        'Airline-Approved Carrier Size M',
        'Airline-approved carrier. Ventilated mesh, rigid base with removable cushion. For pets up to 7 kg.',
    ),
    'Omega 3 para Pelaje Brillante': (
        'Omega 3 for Shiny Coat',
        'Salmon oil capsules rich in EPA and DHA. Improves coat shine, reduces inflammation and supports heart function.',
    ),
    'Probiótico Digestivo Mascotas': (
        'Pet Digestive Probiotic',
        'Blend of 7 probiotic strains + FOS prebiotics. Regulates intestinal flora, reduces gas and improves stool consistency.',
    ),
    'Suplemento Articular Senior': (
        'Senior Joint Supplement',
        'Glucosamine + chondroitin + MSM powder. Reduces joint pain in dogs with arthritis. Chicken flavor. 60 servings.',
    ),
    'Vitaminas Multiespecie': (
        'Multi-Species Vitamins',
        'Vitamin complex A, B, C, D and E plus chelated minerals. Chewable liver-flavored tablets. 90 units.',
    ),
    'Antiparasitario Externo Mensual': (
        'Monthly External Antiparasitic',
        'Monthly spot-on pipette against fleas, ticks and mosquitoes. Safe from 2 months of age. Per dose.',
    ),
    'Crema Cicatrizante para Patas': (
        'Paw Healing Cream',
        'Cream with shea butter, vitamin E and tea tree. Moisturizes and heals cracks in paw pads. Non-toxic if licked.',
    ),
}

# Rangos de peso de mascota (kg) por producto — None = aplica a todos los tamaños
PESO_RANGES = {
    'Concentrado Premium Cachorro':         (2.0,  40.0),
    'Concentrado Adulto Raza Pequeña':      (1.0,  10.0),
    'Alimento Húmedo Gato Pollo 12 latas': (2.0,   8.0),
    'Snack Dental Canino':                  (5.0,  50.0),
    'Croquetas Senior Gato':                (2.0,   8.0),
    'Cuerda Trenzada XL':                   (15.0, 60.0),
    'Disco Volador Flexible':               (10.0, 50.0),
    'Cama Ortopédica Mediana':             (10.0, 30.0),
    'Arnés Ajustable Reflectivo':           (10.0, 22.0),
    'Transportadora Aérea Talla M':         (0.5,   7.0),
    'Suplemento Articular Senior':          (20.0, 80.0),
}

COMMENTS = [
    'Excelente calidad, mi mascota lo amó.',
    'Buen producto, llegó rápido.',
    'Relación precio/calidad muy buena.',
    'Volvería a comprar sin duda.',
    'Superó mis expectativas.',
    'Cumple lo que promete.',
    'Mi veterinario me lo recomendó y quedé encantado.',
    'Lo compré por el precio y me sorprendió la calidad.',
]

# Imágenes de Picsum por categoría (seed fijo = imagen consistente)
CATEGORY_IMG_SEEDS = {
    'dog-food-1':       ('https://picsum.photos/seed/kibble1/400/400',  'concentrado-premium-cachorro.jpg'),
    'dog-food-2':       ('https://picsum.photos/seed/kibble2/400/400',  'concentrado-adulto-raza-pequena.jpg'),
    'cat-food-1':       ('https://picsum.photos/seed/wetfood/400/400',  'alimento-humedo-gato-pollo.jpg'),
    'dog-snack':        ('https://picsum.photos/seed/dogsnack/400/400', 'snack-dental-canino.jpg'),
    'cat-food-2':       ('https://picsum.photos/seed/catsen/400/400',   'croquetas-senior-gato.jpg'),
    'bird-food':        ('https://picsum.photos/seed/birdseed/400/400', 'alimento-semillas-aves.jpg'),
    'dog-ball':         ('https://picsum.photos/seed/dogball/400/400',  'pelota-reforzada-mordible.jpg'),
    'cat-toy-1':        ('https://picsum.photos/seed/catmouse/400/400', 'raton-interactivo-catnip.jpg'),
    'dog-rope':         ('https://picsum.photos/seed/dogrope/400/400',  'cuerda-trenzada-xl.jpg'),
    'cat-tunnel':       ('https://picsum.photos/seed/cattun/400/400',   'tunel-plegable-gatos.jpg'),
    'dog-frisbee':      ('https://picsum.photos/seed/frisbee/400/400',  'disco-volador-flexible.jpg'),
    'dog-puzzle':       ('https://picsum.photos/seed/dogpuzz/400/400',  'dispensador-premios-inteligente.jpg'),
    'cat-litter':       ('https://picsum.photos/seed/litter/400/400',   'arena-aglomerante-lavanda.jpg'),
    'dog-shampoo':      ('https://picsum.photos/seed/shampoo/400/400',  'shampoo-hipoalergenico-canino.jpg'),
    'pet-wipes':        ('https://picsum.photos/seed/wipes/400/400',    'toallitas-humedas-mascotas.jpg'),
    'odor-remover':     ('https://picsum.photos/seed/odor/400/400',     'removedor-olores-enzimatico.jpg'),
    'nail-clipper':     ('https://picsum.photos/seed/nails/400/400',    'cortaunas-profesional.jpg'),
    'dog-brush':        ('https://picsum.photos/seed/brush/400/400',    'cepillo-deslizador-pelo-largo.jpg'),
    'dog-bed':          ('https://picsum.photos/seed/dogbed/400/400',   'cama-ortopedica-mediana.jpg'),
    'dog-harness':      ('https://picsum.photos/seed/harness/400/400',  'arnes-ajustable-reflectivo.jpg'),
    'cat-scratcher':    ('https://picsum.photos/seed/scratch/400/400',  'rascador-torre-compacta.jpg'),
    'slow-feeder':      ('https://picsum.photos/seed/feeder/400/400',   'comedero-antiansiedad.jpg'),
    'id-tag':           ('https://picsum.photos/seed/idtag/400/400',    'placa-identificacion-personalizada.jpg'),
    'pet-carrier':      ('https://picsum.photos/seed/carrier/400/400',  'transportadora-aerea-talla-m.jpg'),
    'omega3':           ('https://picsum.photos/seed/omega3/400/400',   'omega-3-pelaje-brillante.jpg'),
    'probiotic':        ('https://picsum.photos/seed/probio/400/400',   'probiotico-digestivo-mascotas.jpg'),
    'joint-supplement': ('https://picsum.photos/seed/joints/400/400',   'suplemento-articular-senior.jpg'),
    'vitamins':         ('https://picsum.photos/seed/vitamins/400/400', 'vitaminas-multiespecie.jpg'),
    'antiparasitic':    ('https://picsum.photos/seed/antipar/400/400',  'antiparasitario-externo-mensual.jpg'),
    'paw-cream':        ('https://picsum.photos/seed/pawcream/400/400', 'crema-cicatrizante-patas.jpg'),
}


def _download_image(url, filename, stdout):
    """Descarga una imagen y retorna (ContentFile, filename). Retorna (None, None) si falla."""
    try:
        resp = http_client.get(url, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            return ContentFile(resp.content), filename
        stdout.write(f'  [warn] HTTP {resp.status_code} para {url}')
    except Exception as exc:
        stdout.write(f'  [warn] No se pudo descargar imagen: {exc}')
    return None, None


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos demo para Kibo (30 productos con imágenes).'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando seed demo data...'))

        # ── 1) Usuarios demo ──────────────────────────────────────────
        admin_user, _ = User.objects.get_or_create(
            username='kibo_admin',
            defaults={'email': 'admin@kibo.local', 'is_staff': True},
        )
        if not admin_user.check_password('kibo12345'):
            admin_user.set_password('kibo12345')
            admin_user.save()

        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        if not admin_profile.is_admin:
            admin_profile.is_admin = True
            admin_profile.phone = admin_profile.phone or '3000000000'
            admin_profile.address = admin_profile.address or 'Centro Administrativo Kibo'
            admin_profile.save()

        demo_users = []
        for i in range(1, 6):
            username = f'cliente{i}'
            u, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@mail.com'},
            )
            if not u.check_password('kibo12345'):
                u.set_password('kibo12345')
                u.save()
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.is_admin = False
            profile.phone = profile.phone or f'31100000{i:02d}'
            profile.address = profile.address or f'Calle Demo #{i} - Bogotá'
            profile.save()
            demo_users.append(u)

        # ── 2) Categorías ─────────────────────────────────────────────
        category_map = {}
        for c in CATEGORIES:
            slug = slugify(c['name'])
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': c['name'], 'description': c['description']},
            )
            category.name_en = c.get('name_en', '')
            category.save(update_fields=['name_en'])
            category_map[c['name']] = category

        # ── 3) Productos con imágenes ──────────────────────────────────
        products_created = 0
        all_products = []

        for name, cat_name, tipo_mascota, etapa_vida, price, stock, img_seed, description in PRODUCTS:
            slug = slugify(name)
            category = category_map[cat_name]

            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'category': category,
                    'name': name,
                    'description': description,
                    'price': price,
                    'stock': stock,
                    'is_active': True,
                    'tipo_mascota': tipo_mascota,
                    'etapa_vida': etapa_vida,
                },
            )

            peso_min, peso_max = PESO_RANGES.get(name, (None, None))
            name_en, description_en = TRANSLATIONS_EN.get(name, ('', ''))

            if not created:
                product.category = category
                product.price = price
                product.stock = stock
                product.is_active = True
                product.tipo_mascota = tipo_mascota
                product.etapa_vida = etapa_vida
                product.description = description
                product.peso_min_kg = peso_min
                product.peso_max_kg = peso_max
                product.name_en = name_en
                product.description_en = description_en
                product.save()
            else:
                products_created += 1
                product.peso_min_kg = peso_min
                product.peso_max_kg = peso_max
                product.name_en = name_en
                product.description_en = description_en
                product.save(update_fields=['peso_min_kg', 'peso_max_kg', 'name_en', 'description_en'])

            # Descargar imagen si el producto no tiene una
            if not product.image and img_seed in CATEGORY_IMG_SEEDS:
                img_url, img_filename = CATEGORY_IMG_SEEDS[img_seed]
                self.stdout.write(f'  Descargando imagen: {name}...')
                content, filename = _download_image(img_url, img_filename, self.stdout)
                if content:
                    product.image.save(filename, content, save=True)

            all_products.append(product)

        # ── 4) Carritos con items aleatorios ──────────────────────────
        for user in demo_users:
            cart, _ = Cart.objects.get_or_create(user=user)
            if cart.items.count() == 0:
                picks = random.sample(all_products, k=min(4, len(all_products)))
                for p in picks:
                    CartItem.objects.get_or_create(
                        cart=cart,
                        product=p,
                        defaults={'quantity': random.randint(1, 3)},
                    )

        # ── 5) Órdenes demo ───────────────────────────────────────────
        for idx, user in enumerate(demo_users, start=1):
            if user.orders.count() > 0:
                continue
            picks = random.sample(all_products, k=min(3, len(all_products)))
            status = random.choice(['pending', 'confirmed', 'shipped', 'delivered'])
            order = Order.objects.create(
                user=user,
                total=Decimal('0.00'),
                status=status,
                shipping_address=f'Cra Demo {idx} #12-3{idx}, Bogotá',
                payment_method='tarjeta',
            )
            total = Decimal('0.00')
            for p in picks:
                qty = random.randint(1, 2)
                OrderItem.objects.create(
                    order=order, product=p,
                    quantity=qty, unit_price=p.price,
                )
                total += p.price * qty
            order.total = total
            order.save()

        # ── 6) Reviews ────────────────────────────────────────────────
        for user in demo_users:
            picks = random.sample(all_products, k=min(6, len(all_products)))
            for p in picks:
                Review.objects.get_or_create(
                    user=user, product=p,
                    defaults={
                        'rating': random.randint(3, 5),
                        'comment': random.choice(COMMENTS),
                    },
                )

        # ── 7) Wishlist ───────────────────────────────────────────────
        for user in demo_users:
            picks = random.sample(all_products, k=min(5, len(all_products)))
            for p in picks:
                Wishlist.objects.get_or_create(user=user, product=p)

        self.stdout.write(self.style.SUCCESS('\nSeed completado exitosamente.'))
        self.stdout.write(f'  Categorías:          {len(CATEGORIES)}')
        self.stdout.write(f'  Productos totales:   {len(PRODUCTS)}')
        self.stdout.write(f'  Productos nuevos:    {products_created}')
        self.stdout.write(f'  Usuarios demo:       {len(demo_users)} clientes + 1 admin')
        self.stdout.write('\nCredenciales:')
        self.stdout.write('  Admin:    kibo_admin  / kibo12345')
        self.stdout.write('  Cliente:  cliente1..5 / kibo12345')
