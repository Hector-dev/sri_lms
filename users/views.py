from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm
import logging
import json

# Create your views here.

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                
                # Crear notificación de bienvenida
                from core.models import Notification
                Notification.objects.create(
                    user=user,
                    message=f'¡Bienvenido a SRI Learning, {user.username}! Tu cuenta ha sido creada exitosamente.'
                )
                
                messages.success(request, f'Cuenta creada con éxito. ¡Bienvenido {user.username}!')
                return redirect('home')
            except Exception as e:
                logging.error(f"Error al crear usuario: {e}")
                messages.error(request, 'Error al crear la cuenta. Por favor, inténtalo de nuevo.')
    else:
        form = UserRegistrationForm()
        
    context = {'form': form}
    if request.user.is_authenticated:
        from core.models import Notification
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'users/register.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            try:
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    if not remember_me:
                        request.session.set_expiry(0)  # Si no marca recordar, la sesión expira al cerrar navegador
                    messages.success(request, f'¡Bienvenido de nuevo, {username}!')
                    # Redirección según tipo de usuario
                    if user.user_type == 'instructor':
                        return redirect('courses:instructor_dashboard')
                    else:
                        return redirect('users:student_dashboard')
                else:
                    messages.error(request, 'Error en el inicio de sesión. Revise sus credenciales.')
            except Exception as e:
                logging.error(f"Error en login: {e}")
                messages.error(request, 'Error en el inicio de sesión. Por favor, inténtalo de nuevo.')
        else:
            messages.error(request, 'Error en el inicio de sesión. Revise sus credenciales.')
    else:
        form = UserLoginForm()
        
    context = {'form': form}
    if request.user.is_authenticated:
        from core.models import Notification
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'users/login.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')

@login_required
def profile_view(request):
    # Esta vista mostrará el perfil del usuario
    context = {}
    if request.user.is_authenticated:
        from core.models import Notification
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('users:profile')
            except Exception as e:
                logging.error(f"Error al actualizar perfil: {e}")
                messages.error(request, 'Error al actualizar el perfil. Por favor, inténtalo de nuevo.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {'form': form}
    if request.user.is_authenticated:
        from core.models import Notification
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'users/edit_profile.html', context)

@login_required
def student_dashboard(request):
    if request.user.user_type != 'student':
        messages.error(request, 'Solo los estudiantes pueden acceder a este panel.')
        return redirect('home')
    try:
        enrolled_courses = request.user.enrolled_courses.all()
        context = {'enrolled_courses': enrolled_courses}
        if request.user.is_authenticated:
            from core.models import Notification
            context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
        return render(request, 'users/student_dashboard.html', context)
    except Exception as e:
        logging.error(f"Error en student_dashboard: {e}")
        messages.error(request, 'Error al cargar el panel de estudiante.')
        return redirect('home')

@login_required
def notifications_view(request):
    try:
        from core.models import Notification
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        context = {'notifications': notifications}
        if request.user.is_authenticated:
            context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
        return render(request, 'users/notifications.html', context)
    except Exception as e:
        logging.error(f"Error en notifications_view: {e}")
        messages.error(request, 'Error al cargar las notificaciones.')
        return redirect('home')

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Marcar una notificación como leída"""
    try:
        from core.models import Notification
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})
    except Exception as e:
        logging.error(f"Error al marcar notificación como leída: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@require_POST
def mark_all_notifications_read(request):
    """Marcar todas las notificaciones como leídas"""
    try:
        from core.models import Notification
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return JsonResponse({'success': True})
    except Exception as e:
        logging.error(f"Error al marcar todas las notificaciones como leídas: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Eliminar una notificación específica"""
    try:
        from core.models import Notification
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notificación no encontrada'})
    except Exception as e:
        logging.error(f"Error al eliminar notificación: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
@require_POST
def delete_all_notifications(request):
    """Eliminar todas las notificaciones del usuario"""
    try:
        from core.models import Notification
        Notification.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        logging.error(f"Error al eliminar todas las notificaciones: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

@login_required
def update_preferences(request):
    """Actualizar preferencias del usuario via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cookie_updates = {}
            
            # Validar y procesar cada preferencia
            if 'theme' in data and data['theme'] in settings.ALLOWED_THEMES:
                cookie_updates['theme'] = data['theme']
            
            if 'layout' in data and data['layout'] in settings.ALLOWED_LAYOUTS:
                cookie_updates['layout'] = data['layout']
            
            if 'notifications' in data and data['notifications'] in settings.ALLOWED_NOTIFICATIONS:
                cookie_updates['notifications'] = data['notifications']
            
            if 'learning_style' in data and data['learning_style'] in settings.ALLOWED_LEARNING_STYLES:
                cookie_updates['learning_style'] = data['learning_style']
            
            if 'difficulty' in data and data['difficulty'] in settings.ALLOWED_DIFFICULTIES:
                cookie_updates['difficulty'] = data['difficulty']
            
            if 'pace' in data and data['pace'] in settings.ALLOWED_PACES:
                cookie_updates['pace'] = data['pace']
            
            if 'feedback_style' in data and data['feedback_style'] in settings.ALLOWED_FEEDBACK_STYLES:
                cookie_updates['feedback_style'] = data['feedback_style']
            
            if 'analytics' in data and data['analytics'] in settings.ALLOWED_ANALYTICS:
                cookie_updates['analytics'] = data['analytics']
            
            if 'test_preferences' in data and isinstance(data['test_preferences'], dict):
                cookie_updates['test_preferences'] = json.dumps(data['test_preferences'])
            
            # Guardar las actualizaciones en el request para que el middleware las procese
            request.cookie_updates = cookie_updates
            
            response = JsonResponse({
                'success': True,
                'message': 'Preferencias actualizadas correctamente',
                'updates': cookie_updates
            })
            
            # Establecer las cookies en la respuesta
            for cookie_name, cookie_value in cookie_updates.items():
                if cookie_name in settings.CUSTOM_COOKIES:
                    config = settings.CUSTOM_COOKIES[cookie_name]
                    response.set_cookie(
                        name=config['name'],
                        value=cookie_value,
                        max_age=config['max_age'],
                        secure=config['secure'],
                        httponly=config['httponly'],
                        samesite=config['samesite']
                    )
            
            return response
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Error en el formato de datos'
            }, status=400)
        except Exception as e:
            logging.error(f"Error al actualizar preferencias: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)

@login_required
def get_preferences(request):
    """Obtener las preferencias actuales del usuario"""
    try:
        preferences = getattr(request, 'cookie_preferences', {})
        return JsonResponse({
            'success': True,
            'preferences': preferences
        })
    except Exception as e:
        logging.error(f"Error al obtener preferencias: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Error al obtener preferencias'
        }, status=500)
