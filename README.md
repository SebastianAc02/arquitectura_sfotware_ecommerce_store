# Kibo Pet E-commerce

Plataforma de comercio electrónico para tienda de mascotas. Proyecto académico de **Arquitectura de Software (SI3001)** construido con Django 4, PostgreSQL y Docker.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 + Django 4.2 |
| Base de datos | PostgreSQL 15 |
| Containerización | Docker + Docker Compose |
| Frontend | DaisyUI v4 + Tailwind CSS v3 (CDN) |
| Generación de PDF | ReportLab 4.1 |
| HTTP cliente | requests 2.31 |
| Manejo de imágenes | Pillow 10.2 |
| Variables de entorno | python-decouple 3.8 |

---

## Arquitectura general

El proyecto sigue el patrón **MVC** nativo de Django (Model-View-Template), extendido con una capa de servicios y patrones de diseño adicionales.

```
kibo/                        # Configuración principal del proyecto
├── settings.py              # Settings, INSTALLED_APPS, i18n, DB, media
├── urls.py                  # Router raíz — delega a cada app
accounts/                    # Dominio: autenticación, perfiles, mascotas
├── models.py                # User, UserProfile, Mascota
├── views.py                 # login, register, profile, mascotas CRUD
├── forms.py                 # RegisterForm, ProfileUpdateForm, MascotaForm
store/                       # Dominio: catálogo, carrito, checkout, órdenes
├── models.py                # Product, Category, Cart, CartItem, Order, OrderItem, Review, Wishlist
├── views.py                 # home, catalog, product_detail, cart, checkout, orders, razas, API
├── services/                # Capa de servicios (lógica de negocio desacoplada)
│   ├── checkout.py          # CheckoutService — transacciones atómicas
│   └── notifications.py     # NotificationService / MockNotificationService
├── payments/                # Inversión de dependencias — métodos de pago
│   ├── base.py              # MetodoPago (ABC — interfaz abstracta)
│   ├── tarjeta.py           # PagoTarjeta — descuenta saldo virtual
│   └── cheque.py            # PagoCheque — genera PDF con ReportLab
├── context_processors.py    # Inyecta cart_count y cart_total en todos los templates
admin_panel/                 # Panel de administración custom (no Django admin)
├── views.py                 # dashboard, product CRUD, order list
templates/                   # Templates globales (base_public.html, base_admin.html)
locale/                      # Traducciones ES / EN (.po / .mo)
```

---

## Apps del proyecto

### `accounts` — Autenticación y perfiles

Responsable de todo lo relacionado con usuarios:

- **UserProfile**: extiende el `User` de Django via OneToOne (patrón de composición, evita el God User anti-pattern). Campos: `phone`, `address`, `pais` (código ISO), `saldo` (Decimal, saldo virtual para pagos), `is_admin` (rol).
- **Mascota**: entidad registrada por el usuario con nombre, tipo (perro/gato/ave/otro), raza, edad, peso e imagen (ImageField). Un usuario puede tener múltiples mascotas.
- **Señales (Observer pattern)**: `post_save` sobre `User` crea automáticamente el `UserProfile` sin que el User sepa que existe — loose coupling.

### `store` — Tienda

Responsable del catálogo, carrito, checkout y órdenes:

- **Product**: nombre, slug, precio, stock, imagen, categoría, tipo_mascota, is_active. Manager custom con `.activos()`, `.filter_by(GET)`, `.top_vendidos()`.
- **Category**: nombre y slug.
- **Cart / CartItem**: carrito por usuario (OneToOne). Métodos `get_total()` y `get_item_count()` calculados en Python, no en la DB.
- **Order / OrderItem**: snapshot de precio en `unit_price` al momento de compra — el precio del producto puede cambiar después sin afectar órdenes pasadas.
- **Review**: reseña con rating y texto, asociada a product + user.
- **Wishlist**: lista de deseos por usuario.

### `admin_panel` — Panel custom

Panel de administración propio (independiente del Django admin) accesible solo para usuarios con `UserProfile.is_admin = True` o `User.is_superuser = True`.

---

## Patrones de diseño aplicados

### 1. Inversión de Dependencias (DI) — Sistema de pagos

El checkout no depende de ninguna clase concreta de pago:

```python
# MetodoPago es la abstracción (ABC)
class MetodoPago(ABC):
    @abstractmethod
    def procesar_pago(self, orden): ...

# La view instancia la clase concreta según la elección del usuario
if payment_method == 'tarjeta':
    metodo_pago = PagoTarjeta(request.user)   # Implementación 1
else:
    metodo_pago = PagoCheque()                # Implementación 2

# El servicio llama a la interfaz — no sabe qué clase concreta es
resultado = metodo_pago.procesar_pago(order)
```

- **PagoTarjeta**: verifica y descuenta `UserProfile.saldo`. Si el saldo es insuficiente lanza `ValueError`.
- **PagoCheque**: genera un PDF con ReportLab con datos del cheque (monto, beneficiario, fecha, número de orden) y lo retorna como descarga directa (`application/pdf`).

### 2. Service Layer — CheckoutService

La lógica de negocio del checkout está desacoplada de la vista HTTP:

```python
# La vista solo maneja HTTP; el servicio maneja negocio
service = CheckoutService()
order = service.crear_orden_desde_carrito(
    user=request.user,
    cart=cart,
    shipping_address=shipping_address,
    payment_method=payment_method,
)
```

El servicio corre en una transacción atómica: si el stock de algún producto es insuficiente durante el proceso, hace rollback completo.

### 3. Observer Pattern — Señales de Django

```python
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
```

El `User` no sabe que existe `UserProfile`. Acoplamiento cero entre las entidades.

### 4. Context Processor — Datos globales en templates

`store/context_processors.py` inyecta `cart_count` y `cart_total` en cada template automáticamente. Las vistas no necesitan pasarlo manualmente (principio DRY).

### 5. CBV (Class-Based Views)

`ProductDetailView` hereda de `DetailView` — extensible por herencia sin copiar código. El método `get_context_data()` agrega reviews y recomendaciones.

### 6. PRG (Post/Redirect/Get)

Todas las acciones de carrito (agregar, eliminar, actualizar) y login usan el patrón PRG para evitar reenvíos de formulario al recargar la página.

---

## Internacionalización (i18n)

Soporte completo **Español / Inglés** con Django i18n nativo:

- Todos los textos en templates usan `{% trans "..." %}` y `{% blocktrans %}...{% endblocktrans %}`
- Todo el código Python usa `gettext_lazy as _` en mensajes, labels y choices
- Archivos `.po` / `.mo` en `locale/es/` y `locale/en/`
- Selector de idioma en el footer (POST a `set_language`)
- El idioma persiste en sesión vía `LocaleMiddleware`

---

## APIs integradas

### API propia — REST JSON público

```
GET /api/productos/
```

Retorna todos los productos activos con stock > 0. Sin autenticación. Estructura:

```json
{
  "productos": [
    {
      "id": 1,
      "nombre": "Croquetas Premium",
      "precio": "45000.00",
      "categoria": "Alimentos",
      "stock": 20,
      "imagen_url": "http://...",
      "detalle_url": "http://.../producto/croquetas-premium/"
    }
  ]
}
```

### TheDogAPI — Razas de mascotas

```
GET /razas/
```

Consume `https://api.thedogapi.com/v1/breeds` y muestra 12 razas con foto, temperamento, esperanza de vida y peso. Respuesta cacheada en sesión para evitar múltiples llamadas.

### RestCountries — Selector de país

Consume `https://restcountries.com/v3.1/all` al cargar los formularios de registro y perfil. Lista de países ordenada alfabéticamente en español, cacheada en sesión. Guarda el código ISO (cca2) en `UserProfile.pais`.

### API Ninjas — Dato curioso

Widget `¿Sabías que...?` en el home. Consume `https://api.api-ninjas.com/v1/facts` client-side (JavaScript fetch). El usuario puede refrescar el dato con un botón.

---

## Lógica de negocio

### Flujo de compra

1. Usuario agrega productos al carrito (`/carrito/agregar/<slug>/`)
2. Cada adición verifica `product.is_available()` (stock > 0 y is_active = True)
3. En checkout, elige dirección de envío y método de pago (tarjeta o cheque)
4. Si elige **tarjeta**: se verifica que `UserProfile.saldo >= total`. Si pasa, `CheckoutService` crea la orden y `PagoTarjeta.procesar_pago()` descuenta el saldo
5. Si elige **cheque**: `CheckoutService` crea la orden y `PagoCheque.procesar_pago()` retorna un PDF descargable directamente
6. El stock de cada producto se descuenta atómicamente en la misma transacción

### Roles y acceso

- **Cliente** (`is_admin=False`, `is_superuser=False`): acceso a tienda, carrito, checkout, perfil, mascotas
- **Administrador de dominio** (`UserProfile.is_admin=True`): acceso al panel custom + todo lo anterior
- **Superusuario** (`User.is_superuser=True`): mismo acceso que admin de dominio + Django admin en `/django-admin/`
- El botón "Panel admin" en el navbar es visible para cualquiera de los dos roles

### Mascotas

Cada usuario puede registrar sus mascotas con nombre, tipo, raza, edad, peso y foto. El sistema ofrece sugerencias de razas bilingües (ES/EN) via `<datalist>` con listas estáticas en JavaScript.

---

## Pruebas unitarias

```bash
docker compose exec web python manage.py test
```

12 tests en `store/tests.py`:

| Clase | Tests |
|---|---|
| `RequisitosEntregable2TestCase` | `test_producto_sin_stock_no_agrega_carrito`, `test_precio_producto_mayor_cero` |
| `ProductStockTestCase` | `test_reduce_stock_descuenta_correctamente`, `test_is_available_con_stock`, `test_is_available_sin_stock`, `test_is_available_inactivo` |
| `CheckoutServiceTestCase` | `test_checkout_descuenta_stock_correctamente`, `test_checkout_crea_orden_con_total_correcto`, `test_checkout_vacia_el_carrito`, `test_checkout_falla_si_stock_insuficiente`, `test_checkout_no_modifica_stock_si_falla`, `test_checkout_snapshot_precio_unit_price` |

---

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/` | Home — productos destacados + categorías + widget dato curioso |
| `/catalogo/` | Catálogo con filtros por categoría/tipo/precio y paginación |
| `/producto/<slug>/` | Detalle de producto con reseñas y recomendaciones |
| `/razas/` | Razas de mascotas (TheDogAPI) |
| `/carrito/` | Carrito del usuario |
| `/checkout/` | Checkout con DI (tarjeta virtual / cheque PDF) |
| `/mis-ordenes/` | Historial de órdenes con paginación |
| `/api/productos/` | JSON público de productos en stock |
| `/accounts/login/` | Inicio de sesión |
| `/accounts/register/` | Registro + selector de país (RestCountries) |
| `/accounts/profile/` | Perfil editable + saldo virtual + país |
| `/accounts/mascotas/` | CRUD de mascotas |
| `/panel/` | Panel admin custom |
| `/django-admin/` | Django admin built-in |

---

## Variables de entorno (`.env`)

```env
SECRET_KEY=django-insecure-kibo-dev-key-change-in-prod
DEBUG=True
DB_NAME=kibo_db
DB_USER=kibo_user
DB_PASSWORD=kibo_pass
DB_HOST=db
DB_PORT=5432
```

`DB_HOST=db` es el nombre del servicio en `docker-compose.yml`. No subir `.env` al repositorio.

---

## Levantar el proyecto

```bash
# 1. Clonar
git clone https://github.com/SebastianAc02/arquitectura_sfotware_ecommerce.git
cd arquitectura_sfotware_ecommerce

# 2. Crear .env (ver sección anterior)

# 3. Construir y levantar
docker compose up -d --build

# 4. Migraciones
docker compose exec web python manage.py migrate

# 5. (Opcional) Datos demo
docker compose exec web python manage.py seed_demo_data

# 6. Abrir
# http://localhost:8000
```

---

## Comandos frecuentes

```bash
# Crear migraciones después de cambiar modelos
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Compilar traducciones después de editar .po
docker compose exec web python manage.py compilemessages

# Extraer nuevos strings a traducir
docker compose exec web python manage.py makemessages -l es
docker compose exec web python manage.py makemessages -l en

# Ejecutar tests
docker compose exec web python manage.py test

# Shell de Django
docker compose exec web python manage.py shell

# Logs
docker compose logs -f web

# Reset completo de base de datos
docker compose down -v && docker compose up -d --build && docker compose exec web python manage.py migrate
```

---

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| Puerto 8000 ocupado | Otro proceso usa el puerto | `docker compose down` o cambiar puerto en `docker-compose.yml` |
| Error de conexión a PostgreSQL | `DB_HOST` incorrecto | Verificar que `.env` tenga `DB_HOST=db` cuando se usa Docker |
| Cambios en templates no se reflejan | Cache de Docker | `docker compose up -d --build` |
| Error de migración | Modelo cambiado sin migrar | `makemigrations` + `migrate` |
| `ModuleNotFoundError` en contenedor | Paquete nuevo sin reconstruir | `docker compose build --no-cache web && docker compose up -d` |
