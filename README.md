# Panel de Administración Django Reutilizable

Este es un panel de administración modular y reutilizable para Django que incluye autenticación de dos factores, gestión de usuarios y recuperación de contraseña.

## Características

- Autenticación de dos factores (2FA) con códigos por email
- Sistema de roles (Admin, Usuario, Staff)
- Recuperación de contraseña segura
- Rate limiting para prevenir ataques
- Sistema de mensajes para feedback
- Interfaz responsive
- Fácilmente personalizable

## Requisitos

- Python 3.8+
- Django 4.0+
- django-ratelimit
- Pillow (para manejo de imágenes)
- django-encrypted-model-fields

## Instalación

1. Copia la carpeta del módulo en tu proyecto Django
2. Agrega el módulo a INSTALLED_APPS en settings.py:

```python
INSTALLED_APPS = [
    ...
    'tu_modulo',
    ...
]
```

3. Configura las variables de email en settings.py:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'tu_servidor_smtp'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email'
EMAIL_HOST_PASSWORD = 'tu_password'
DEFAULT_FROM_EMAIL = 'tu_email'
```

4. Agrega las URLs en tu urls.py:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('', include('tu_modulo.url')),
    ...
]
```

5. Ejecuta las migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Personalización

### Roles

Los roles por defecto son:
- admin: Administrador del sistema
- user: Usuario normal
- staff: Personal del sistema

Puedes modificar los roles en models.py:

```python
ROLES = [
    ('admin', 'Administrador'),
    ('user', 'Usuario'),
    ('staff', 'Personal'),
    # Agrega tus roles personalizados aquí
]
```

### Templates

Los templates se encuentran en la carpeta templates/ y puedes personalizarlos según tus necesidades:

- account/login.html
- account/registro.html
- account/verificar_codigo.html
- panel/admin_dashboard.html
- panel/user_dashboard.html
- panel/staff_dashboard.html
- reset_password/*.html

### Estilos

Los estilos se encuentran en la carpeta static/ y puedes modificarlos según tu diseño.

## Uso

### Crear un superusuario

```bash
python manage.py createsuperuser
```

### Decoradores

El módulo incluye un decorador para control de acceso basado en roles:

```python
from tu_modulo.decorators import solo_rol

@solo_rol('admin')
def tu_vista(request):
    ...
```

### Mensajes

El sistema usa el framework de mensajes de Django:

```python
from django.contrib import messages

messages.success(request, "Operación exitosa")
messages.error(request, "Error en la operación")
messages.info(request, "Información importante")
```

## Seguridad

- Autenticación de dos factores
- Rate limiting en login y recuperación de contraseña
- Contraseñas encriptadas
- Tokens seguros para recuperación de contraseña
- Control de acceso basado en roles

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crea un Pull Request

## Licencia

MIT 