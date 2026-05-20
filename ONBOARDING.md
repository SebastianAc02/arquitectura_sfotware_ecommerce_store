# Onboarding — Kibo Pet E-commerce

Guía para que cualquier integrante del equipo pueda entender el proyecto, levantarlo y empezar a contribuir en el menor tiempo posible.

---

## ¿Qué es Kibo?

Kibo es una tienda online de productos para mascotas construida con Django. Proyecto académico para el curso **Arquitectura de Software (SI3001)**. El stack es Django 4 + PostgreSQL + Docker, con DaisyUI/Tailwind para el frontend.

Los usuarios pueden explorar el catálogo, agregar productos al carrito, hacer checkout (pago con tarjeta virtual o cheque PDF), ver su historial de órdenes, registrar sus mascotas y cambiar el idioma entre español e inglés.

---

## Requisitos previos

Solo necesitas dos cosas instaladas en tu máquina:

1. **Docker Desktop** — descárgalo en [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. **Git**

Verifica que funcionan:

```bash
docker --version        # Docker Desktop 4.x
docker compose version  # v2.x
git --version
```

No necesitas instalar Python, PostgreSQL ni ninguna dependencia más — Docker lo maneja todo.

---

## Levantar el proyecto por primera vez

### Paso 1 — Clonar

```bash
git clone https://github.com/SebastianAc02/arquitectura_sfotware_ecommerce.git
cd arquitectura_sfotware_ecommerce
```

### Paso 2 — Crear el archivo `.env`

Crea un archivo llamado `.env` en la raíz del proyecto con este contenido:

```env
SECRET_KEY=django-insecure-kibo-dev-key-change-in-prod
DEBUG=True
DB_NAME=kibo_db
DB_USER=kibo_user
DB_PASSWORD=kibo_pass
DB_HOST=db
DB_PORT=5432
```

> `DB_HOST=db` es el nombre del contenedor de PostgreSQL en Docker Compose. No uses `localhost` aquí.

### Paso 3 — Levantar Docker

```bash
docker compose up -d --build
```

Esto descarga las imágenes (solo la primera vez tarda), construye el contenedor de Django y levanta PostgreSQL.

### Paso 4 — Aplicar migraciones

```bash
docker compose exec web python manage.py migrate
```

### Paso 5 — Cargar datos demo (recomendado)

```bash
docker compose exec web python manage.py seed_demo_data
```

Esto crea categorías, productos de ejemplo, usuarios de prueba y un admin.

### Paso 6 — Abrir la app

Abre tu navegador en: **http://localhost:8000**

---

## Credenciales de prueba (después de seed_demo_data)

| Rol | Usuario | Contraseña | Acceso |
|---|---|---|---|
| Admin de dominio | `kibo_admin` | `kibo12345` | Panel admin + tienda |
| Cliente demo | `cliente1` a `cliente5` | `kibo12345` | Tienda completa |

Para crear tu propio superusuario:

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Estructura del proyecto

```
arquitectura_sfotware_ecommerce_store/
│
├── kibo/                    # Configuración del proyecto
│   ├── settings.py          # Settings: DB, i18n, apps, media, auth
│   ├── urls.py              # URLs raíz (delega a accounts/, store/, panel/)
│   └── wsgi.py
│
├── accounts/                # App: usuarios, perfiles y mascotas
│   ├── models.py            # UserProfile, Mascota
│   ├── views.py             # login, register, profile, mascotas CRUD
│   ├── forms.py             # RegisterForm, ProfileUpdateForm, MascotaForm
│   ├── urls.py
│   └── templates/accounts/  # login.html, register.html, profile.html, mascota_*.html
│
├── store/                   # App: tienda, carrito, checkout, órdenes
│   ├── models.py            # Product, Category, Cart, Order, Review, Wishlist
│   ├── views.py             # home, catalog, checkout, razas, API JSON
│   ├── forms.py
│   ├── urls.py
│   ├── context_processors.py  # cart_count + cart_total globales
│   ├── services/            # Lógica de negocio
│   │   ├── checkout.py      # CheckoutService (transacciones atómicas)
│   │   └── notifications.py # NotificationService / MockNotificationService
│   ├── payments/            # Inversión de dependencias
│   │   ├── base.py          # MetodoPago (ABC)
│   │   ├── tarjeta.py       # PagoTarjeta
│   │   └── cheque.py        # PagoCheque (ReportLab)
│   └── templates/store/     # home, catalog, cart, checkout, razas, etc.
│
├── admin_panel/             # App: panel de administración custom
│   ├── views.py
│   └── templates/admin_panel/
│
├── templates/               # Templates globales
│   ├── base_public.html     # Navbar + footer para la tienda pública
│   └── base_admin.html      # Base para el panel admin
│
├── locale/                  # Traducciones
│   ├── es/django.po
│   └── en/django.po
│
├── media/                   # Uploads de usuarios (fotos de productos y mascotas)
├── static/                  # Archivos estáticos
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env                     # NO commitear
└── manage.py
```

---

## Flujo de trabajo diario

### Levantar después de haber cerrado la máquina

```bash
docker compose up -d
```

### Bajar los contenedores

```bash
docker compose down
```

### Ver logs en tiempo real

```bash
docker compose logs -f web
```

### Cuando alguien del equipo agrega un modelo nuevo

```bash
git pull
docker compose exec web python manage.py migrate
```

### Cuando tú agregas un modelo nuevo

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### Cuando alguien agrega una dependencia nueva a `requirements.txt`

```bash
docker compose up -d --build
```

---

## ¿Cómo agregar una funcionalidad nueva?

### Ejemplo: agregar un modelo

1. Define el modelo en `store/models.py` o `accounts/models.py`
2. Ejecuta `makemigrations` y `migrate`
3. Crea o actualiza el formulario en `forms.py`
4. Agrega la vista en `views.py`
5. Agrega la URL en `urls.py`
6. Crea el template en `templates/<app>/`

### Ejemplo: agregar una traducción

1. Envuelve el texto con `{% trans "..." %}` en el template o `_('...')` en Python
2. Ejecuta `makemessages`:
   ```bash
   docker compose exec web python manage.py makemessages -l es
   docker compose exec web python manage.py makemessages -l en
   ```
3. Edita los archivos `.po` en `locale/es/` y `locale/en/` con la traducción
4. Compila:
   ```bash
   docker compose exec web python manage.py compilemessages
   ```

### Ejemplo: agregar un test

Los tests viven en `store/tests.py` o `accounts/tests.py`. Hereda de `django.test.TestCase`:

```python
class MiTestCase(TestCase):
    def setUp(self):
        # setup del test
        pass

    def test_mi_funcionalidad(self):
        self.assertEqual(resultado, esperado)
```

Ejecutar tests:

```bash
docker compose exec web python manage.py test
docker compose exec web python manage.py test store  # solo una app
```

---

## Convenciones del proyecto

### Código Python

- Las vistas usan `gettext_lazy as _` para todos los mensajes al usuario
- La lógica de negocio va en `services/`, no en las vistas
- Las vistas solo manejan HTTP: validar input, llamar al servicio, retornar respuesta
- Los formularios usan `ModelForm` donde sea posible
- Los modelos tienen métodos de negocio (`is_available()`, `get_total()`, etc.)

### Templates

- Todos los templates extienden `base_public.html` o `base_admin.html`
- Los textos visibles usan `{% trans "..." %}` siempre
- Los campos de formulario usan clases de DaisyUI (`input input-bordered`, `select select-bordered`, `btn`, etc.)
- El color principal de la marca es `#3b3028` (marrón oscuro)

### Git

- Un commit por funcionalidad o fix
- Mensajes en español, formato: `feat:`, `fix:`, `docs:`, `refactor:`
- Todos los integrantes deben tener commits en el repositorio

---

## Funcionalidades implementadas

### Entregable 1
- Catálogo de productos con filtros (categoría, tipo de mascota, precio)
- Carrito de compras con CRUD de items
- Checkout y generación de órdenes
- Historial de órdenes con paginación
- Registro, login y perfil de usuario
- Panel de administración custom (CRUD de productos, listado de órdenes)
- Mascotas: CRUD completo con foto, razas bilingües, campo por tipo
- Roles: cliente / admin de dominio / superusuario
- Docker con PostgreSQL

### Entregable 2
- **i18n completo**: Español / Inglés con selector en el footer
- **API JSON propia**: `GET /api/productos/` pública y documentada
- **TheDogAPI**: página `/razas/` con tarjetas de razas de perros
- **RestCountries**: selector de país en registro y perfil (cacheado en sesión)
- **API Ninjas**: widget `¿Sabías que...?` en home con dato curioso de animales
- **Inversión de Dependencias**: `MetodoPago` ABC + `PagoTarjeta` (saldo virtual) + `PagoCheque` (PDF ReportLab)
- **Pruebas unitarias**: 12 tests cubriendo stock, checkout y lógica de negocio
- **Navbar redesign**: logo + carrito con total + dropdown de cuenta + botón Panel admin (solo admins/superusuarios)

---

## Preguntas frecuentes

**¿Por qué `DB_HOST=db` y no `localhost`?**
Porque en Docker Compose los servicios se comunican por nombre de servicio. El contenedor de Django ve a PostgreSQL como `db` (el nombre definido en `docker-compose.yml`).

**¿Dónde se guardan las fotos subidas por usuarios?**
En la carpeta `media/` de la raíz. En Docker el volumen está mapeado al host, así que las fotos persisten aunque reinicies el contenedor.

**¿Cómo cambio el idioma de la app?**
Desde el selector ES/EN en el footer. El idioma se guarda en sesión.

**¿Cómo accedo al Django admin built-in?**
En `/django-admin/`. Solo funciona con usuarios que tienen `is_staff=True` o `is_superuser=True`.

**¿Cómo reseteo toda la base de datos?**
```bash
docker compose down -v
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo_data
```

**¿Por qué el saldo virtual del checkout empieza en $1000?**
Es el valor por defecto del campo `UserProfile.saldo`. En producción real se manejaría diferente; en este entorno de demo facilita probar el flujo de pago con tarjeta sin configuración adicional.

**¿Qué pasa si la API de RestCountries o TheDogAPI no responde?**
Las vistas tienen `try/except` con timeout de 5 segundos. Si falla, muestran un mensaje amigable en lugar de un error 500. La lista de países en sesión evita llamadas repetidas.
