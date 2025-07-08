from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class CookiePreferencesMiddleware:
    """
    Middleware para manejar las preferencias de cookies del usuario.
    Procesa las cookies antes de la vista y las establece después.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Procesar cookies antes de la vista
        request.cookie_preferences = self.get_cookie_preferences(request)
        
        response = self.get_response(request)
        
        # Establecer cookies después de la vista si es necesario
        self.set_cookie_preferences(response, request)
        
        return response

    def get_cookie_preferences(self, request):
        """Obtiene las preferencias de cookies del usuario"""
        try:
            return {
                'theme': self._get_valid_cookie(request, 'sri_theme', 'light', settings.ALLOWED_THEMES),
                'layout': self._get_valid_cookie(request, 'sri_layout', 'comfortable', settings.ALLOWED_LAYOUTS),
                'notifications': self._get_valid_cookie(request, 'sri_notifications', 'enabled', settings.ALLOWED_NOTIFICATIONS),
                'learning_style': self._get_valid_cookie(request, 'sri_learning_style', 'visual', settings.ALLOWED_LEARNING_STYLES),
                'difficulty': self._get_valid_cookie(request, 'sri_difficulty', 'beginner', settings.ALLOWED_DIFFICULTIES),
                'pace': self._get_valid_cookie(request, 'sri_pace', 'normal', settings.ALLOWED_PACES),
                'test_preferences': self._get_json_cookie(request, 'sri_test_prefs', {}),
                'feedback_style': self._get_valid_cookie(request, 'sri_feedback', 'detailed', settings.ALLOWED_FEEDBACK_STYLES),
                'analytics': self._get_valid_cookie(request, 'sri_analytics', 'enabled', settings.ALLOWED_ANALYTICS),
            }
        except Exception as e:
            logger.error(f"Error al obtener preferencias de cookies: {e}")
            return self._get_default_preferences()

    def _get_valid_cookie(self, request, cookie_name, default_value, allowed_values):
        """Obtiene una cookie y valida que su valor esté permitido"""
        value = request.COOKIES.get(cookie_name, default_value)
        return value if value in allowed_values else default_value

    def _get_json_cookie(self, request, cookie_name, default_value):
        """Obtiene una cookie JSON y la parsea"""
        try:
            value = request.COOKIES.get(cookie_name)
            if value:
                return json.loads(value)
            return default_value
        except (json.JSONDecodeError, TypeError):
            return default_value

    def _get_default_preferences(self):
        """Retorna las preferencias por defecto"""
        return {
            'theme': 'light',
            'layout': 'comfortable',
            'notifications': 'enabled',
            'learning_style': 'visual',
            'difficulty': 'beginner',
            'pace': 'normal',
            'test_preferences': {},
            'feedback_style': 'detailed',
            'analytics': 'enabled',
        }

    def set_cookie_preferences(self, response, request):
        """Establece las cookies según las preferencias del usuario"""
        try:
            # Solo establecer cookies si el usuario está autenticado o si hay cambios específicos
            if hasattr(request, 'cookie_updates') and request.cookie_updates:
                for cookie_name, cookie_value in request.cookie_updates.items():
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
        except Exception as e:
            logger.error(f"Error al establecer cookies: {e}")

    def process_exception(self, request, exception):
        """Maneja excepciones en el middleware"""
        logger.error(f"Excepción en CookiePreferencesMiddleware: {exception}")
        return None 