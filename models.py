# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import datetime
from encrypted_model_fields.fields import EncryptedCharField

# ---------------------------
# Usuario personalizado
# ---------------------------
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('user', 'Usuario'),
        ('staff', 'Personal'),
    ]

    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    rol = models.CharField(max_length=20, choices=ROLES, default='user')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'rol']

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombre} ({self.rol})"
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_creacion']

class CodigoVerificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='codigo_verificacion_user')
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, default='login')  # login, password_reset, etc.

    def es_valido(self):
        return timezone.now() < self.creado_en + datetime.timedelta(minutes=5)
    
    class Meta:
        verbose_name = 'Código de Verificación'
        verbose_name_plural = 'Códigos de Verificación'
        ordering = ['-creado_en']

class PasswordRecoveryAttempt(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='password_recovery_attempts_user')
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {'Exitoso' if self.success else 'Fallido'}"

    class Meta:
        verbose_name = 'Intento de Recuperación'
        verbose_name_plural = 'Intentos de Recuperación'
        ordering = ['-timestamp']
    