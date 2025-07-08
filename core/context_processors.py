from core.models import Notification
from django.conf import settings

def unread_notifications(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(user=request.user, read=False)
        return {'unread_notifications': unread}
    return {'unread_notifications': []}

def cookie_preferences(request):
    """Proporciona preferencias de cookies a todas las plantillas"""
    try:
        cookie_prefs = getattr(request, 'cookie_preferences', {})
        return {
            'cookie_preferences': cookie_prefs,
            'available_themes': settings.ALLOWED_THEMES,
            'available_layouts': settings.ALLOWED_LAYOUTS,
            'available_notifications': settings.ALLOWED_NOTIFICATIONS,
            'available_learning_styles': settings.ALLOWED_LEARNING_STYLES,
            'available_difficulties': settings.ALLOWED_DIFFICULTIES,
            'available_paces': settings.ALLOWED_PACES,
            'available_feedback_styles': settings.ALLOWED_FEEDBACK_STYLES,
            'available_analytics': settings.ALLOWED_ANALYTICS,
            'current_theme': cookie_prefs.get('theme', 'light'),
            'current_layout': cookie_prefs.get('layout', 'comfortable'),
            'current_notifications': cookie_prefs.get('notifications', 'enabled'),
            'current_learning_style': cookie_prefs.get('learning_style', 'visual'),
            'current_difficulty': cookie_prefs.get('difficulty', 'beginner'),
            'current_pace': cookie_prefs.get('pace', 'normal'),
            'current_feedback_style': cookie_prefs.get('feedback_style', 'detailed'),
            'current_analytics': cookie_prefs.get('analytics', 'enabled'),
        }
    except Exception as e:
        # En caso de error, retornar valores por defecto
        return {
            'cookie_preferences': {},
            'available_themes': ['light', 'dark', 'auto'],
            'available_layouts': ['compact', 'comfortable'],
            'available_notifications': ['enabled', 'disabled'],
            'available_learning_styles': ['visual', 'auditory', 'kinesthetic'],
            'available_difficulties': ['beginner', 'intermediate', 'advanced'],
            'available_paces': ['slow', 'normal', 'fast'],
            'available_feedback_styles': ['detailed', 'summary', 'minimal'],
            'available_analytics': ['enabled', 'disabled'],
            'current_theme': 'light',
            'current_layout': 'comfortable',
            'current_notifications': 'enabled',
            'current_learning_style': 'visual',
            'current_difficulty': 'beginner',
            'current_pace': 'normal',
            'current_feedback_style': 'detailed',
            'current_analytics': 'enabled',
        } 