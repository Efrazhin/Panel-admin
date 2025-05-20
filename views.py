from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import string
from django.contrib import messages
from .forms import LoginForm, RegistroForm, PasswordResetForm, CodeVerificationForm, CustomSetPasswordForm
from .models import Usuario, CodigoVerificacion
import random
from django.core.mail import send_mail
from .decorators import solo_rol

User = get_user_model()

def get_dashboard_url(rol):
    """Función auxiliar para obtener la URL del dashboard según el rol"""
    dashboards = {
        'admin': 'admin_dashboard',
        'user': 'user_dashboard',
        'staff': 'staff_dashboard'
    }
    return dashboards.get(rol, 'default_dashboard')

@login_required
def dashboard_view(request):
    """Vista genérica de dashboard que redirige según el rol"""
    rol = request.user.rol
    dashboard_url = get_dashboard_url(rol)
    return redirect(dashboard_url)

@login_required
@solo_rol('admin')
def admin_dashboard(request):
    return render(request, "panel/admin_dashboard.html")

@login_required
@solo_rol('user')
def user_dashboard(request):
    return render(request, "panel/user_dashboard.html")

@login_required
@solo_rol('staff')
def staff_dashboard(request):
    return render(request, "panel/staff_dashboard.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')

def acceso_denegado(request):
    return render(request, "acceso_denegado.html")

@login_required
def registro_view(request):
    if not request.user.is_staff:
        messages.error(request, "No tienes permiso para registrar usuarios.")
        return redirect('acceso_denegado')

    if request.method == "POST":
        form = RegistroForm(request.POST, request.FILES or None)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Usuario registrado exitosamente.")
            return redirect('admin_dashboard')
        messages.error(request, "Hubo un error en el registro.")
    else:
        form = RegistroForm()

    return render(request, "account/registro.html", {"form": form})

@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def login_view(request):
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(request, 'Demasiados intentos. Intenta nuevamente más tarde.')
        return redirect('login')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            usuario = authenticate(request, username=email, password=password)

            if usuario is not None:
                if not usuario.is_active:
                    messages.error(request, "Tu cuenta está desactivada.")
                    return redirect('login')

                # Generar código de verificación
                codigo = str(random.randint(100000, 999999))
                CodigoVerificacion.objects.create(
                    usuario=usuario, 
                    codigo=codigo,
                    tipo='login'
                )

                # Enviar código por email
                send_mail(
                    'Tu código de verificación',
                    f'Tu código es: {codigo}',
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=False,
                )

                request.session['pre_2fa_user_id'] = usuario.id
                messages.info(request, "Se envió un código de verificación a tu email.")
                return redirect('verificar_codigo')

            messages.error(request, "Email o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, "account/login.html", {"form": form})

def verificar_codigo_view(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")
        user_id = request.session.get('pre_2fa_user_id')

        if not user_id:
            messages.error(request, "Sesión inválida.")
            return redirect('login')

        try:
            usuario = User.objects.get(id=user_id)
            verif = CodigoVerificacion.objects.filter(
                usuario=usuario, 
                codigo=codigo,
                tipo='login'
            ).latest('creado_en')

            if verif.es_valido():
                login(request, usuario)
                usuario.ultimo_acceso = timezone.now()
                usuario.save()
                request.session.pop('pre_2fa_user_id', None)
                messages.success(request, f"¡Bienvenido, {usuario.nombre}!")
                return redirect(get_dashboard_url(usuario.rol))
            else:
                messages.error(request, "El código ha expirado.")
        except (User.DoesNotExist, CodigoVerificacion.DoesNotExist):
            messages.error(request, "Código inválido.")

    return render(request, "account/verificar_codigo.html")

# Funciones de recuperación de contraseña
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "El correo no está registrado.")
                return redirect('password_reset')

            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            expiration = timezone.now() + timedelta(minutes=5)

            request.session['password_reset_code'] = code
            request.session['password_reset_code_expiration'] = expiration.isoformat()
            request.session['password_reset_email'] = email

            send_mail(
                subject='Código de verificación para restablecer contraseña',
                message=f'Tu código es: {code}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return redirect('password_reset_verify')
    else:
        form = PasswordResetForm()

    return render(request, 'reset_password/password_reset_form.html', {'form': form})

@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@ratelimit(key='post:email', rate='3/h', method='POST', block=True)
def password_reset_verify(request):
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(request, 'Demasiados intentos. Intenta nuevamente más tarde.')
        return redirect('password_reset')

    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            stored_code = request.session.get('password_reset_code')
            expiration_str = request.session.get('password_reset_code_expiration')
            email = request.session.get('password_reset_email')

            if not all([stored_code, expiration_str, email]):
                messages.error(request, "Sesión inválida. Por favor vuelve a empezar.")
                return redirect('password_reset')

            expiration_time = datetime.fromisoformat(expiration_str)

            if code == stored_code and timezone.now() < expiration_time:
                user = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                request.session.flush()
                return redirect('password_reset_change', uidb64=uid, token=token)
            else:
                messages.error(request, "Código inválido o expirado.")
    else:
        form = CodeVerificationForm()

    return render(request, 'reset_password/password_reset_verify.html', {'form': form})

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def password_reset_change(request, uidb64, token):
    UserModel = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Contraseña cambiada correctamente.")
                return redirect('password_reset_complete')
        else:
            form = CustomSetPasswordForm(user)

        return render(request, 'reset_password/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "El enlace es inválido o ha expirado.")
        return redirect('password_reset')

def password_reset_complete(request):
    return render(request, 'reset_password/password_reset_complete.html')
