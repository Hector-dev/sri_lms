from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Prueba el sistema de cookies y preferencias del usuario'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nombre de usuario para probar (opcional)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Iniciando pruebas del sistema de cookies...')
        )

        # Crear cliente de prueba
        client = Client()

        # Obtener o crear usuario de prueba
        username = options['username'] or 'testuser_cookies'
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'✅ Usuario encontrado: {username}')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@test.com',
                password='testpass123',
                user_type='student'
            )
            self.stdout.write(f'✅ Usuario creado: {username}')

        # 1. Probar login
        self.stdout.write('\n🔐 Probando login...')
        login_success = client.login(username=username, password='testpass123')
        if login_success:
            self.stdout.write(self.style.SUCCESS('✅ Login exitoso'))
        else:
            self.stdout.write(self.style.ERROR('❌ Error en login'))
            return

        # 2. Probar obtención de preferencias
        self.stdout.write('\n📋 Probando obtención de preferencias...')
        response = client.get('/users/preferences/get/')
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                self.stdout.write(self.style.SUCCESS('✅ Preferencias obtenidas correctamente'))
                self.stdout.write(f'   Tema actual: {data["preferences"].get("theme", "N/A")}')
                self.stdout.write(f'   Layout actual: {data["preferences"].get("layout", "N/A")}')
            else:
                self.stdout.write(self.style.ERROR('❌ Error al obtener preferencias'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Error HTTP: {response.status_code}'))

        # 3. Probar actualización de preferencias
        self.stdout.write('\n⚙️ Probando actualización de preferencias...')
        
        # Datos de prueba
        test_preferences = {
            'theme': 'dark',
            'layout': 'compact',
            'notifications': 'enabled',
            'learning_style': 'visual',
            'difficulty': 'intermediate',
            'pace': 'normal',
            'feedback_style': 'detailed',
            'analytics': 'enabled'
        }

        response = client.post(
            '/users/preferences/update/',
            data=json.dumps(test_preferences),
            content_type='application/json'
        )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                self.stdout.write(self.style.SUCCESS('✅ Preferencias actualizadas correctamente'))
                self.stdout.write(f'   Actualizaciones: {len(data["updates"])} preferencias')
                
                # Verificar cookies establecidas
                cookies_set = []
                for cookie_name in settings.CUSTOM_COOKIES.keys():
                    if cookie_name in data['updates']:
                        cookies_set.append(cookie_name)
                
                self.stdout.write(f'   Cookies establecidas: {", ".join(cookies_set)}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error: {data.get("message", "Error desconocido")}'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Error HTTP: {response.status_code}'))

        # 4. Probar diferentes temas
        self.stdout.write('\n🎨 Probando diferentes temas...')
        themes = ['light', 'dark', 'auto']
        
        for theme in themes:
            test_data = {'theme': theme}
            response = client.post(
                '/users/preferences/update/',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.stdout.write(self.style.SUCCESS(f'✅ Tema "{theme}" aplicado correctamente'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Error al aplicar tema "{theme}"'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error HTTP al aplicar tema "{theme}": {response.status_code}'))

        # 5. Probar validación de datos
        self.stdout.write('\n🔍 Probando validación de datos...')
        
        # Datos inválidos
        invalid_preferences = {
            'theme': 'invalid_theme',
            'layout': 'invalid_layout',
            'notifications': 'invalid_option'
        }

        response = client.post(
            '/users/preferences/update/',
            data=json.dumps(invalid_preferences),
            content_type='application/json'
        )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                # Verificar que solo se aplicaron valores válidos
                valid_updates = len(data['updates'])
                if valid_updates == 0:
                    self.stdout.write(self.style.SUCCESS('✅ Validación funcionando: no se aplicaron valores inválidos'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️ Se aplicaron {valid_updates} valores válidos'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Error en validación: {data.get("message", "Error desconocido")}'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Error HTTP en validación: {response.status_code}'))

        # 6. Probar middleware
        self.stdout.write('\n🔧 Probando middleware de cookies...')
        
        # Hacer una petición a la página principal
        response = client.get('/')
        
        if response.status_code == 200:
            # Verificar que el middleware procesó las cookies
            if hasattr(response, 'cookies'):
                cookie_count = len(response.cookies)
                self.stdout.write(self.style.SUCCESS(f'✅ Middleware funcionando: {cookie_count} cookies procesadas'))
            else:
                self.stdout.write(self.style.WARNING('⚠️ No se detectaron cookies en la respuesta'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Error al acceder a la página principal: {response.status_code}'))

        # 7. Verificar configuración
        self.stdout.write('\n⚙️ Verificando configuración...')
        
        # Verificar settings
        required_settings = [
            'CUSTOM_COOKIES',
            'ALLOWED_THEMES',
            'ALLOWED_LAYOUTS',
            'ALLOWED_NOTIFICATIONS',
            'ALLOWED_LEARNING_STYLES',
            'ALLOWED_DIFFICULTIES',
            'ALLOWED_PACES',
            'ALLOWED_FEEDBACK_STYLES',
            'ALLOWED_ANALYTICS'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                self.stdout.write(self.style.SUCCESS(f'✅ {setting} configurado'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ {setting} no configurado'))

        # Verificar middleware
        if 'core.middleware.CookiePreferencesMiddleware' in settings.MIDDLEWARE:
            self.stdout.write(self.style.SUCCESS('✅ CookiePreferencesMiddleware registrado'))
        else:
            self.stdout.write(self.style.ERROR('❌ CookiePreferencesMiddleware no registrado'))

        # Verificar context processor
        context_processors = [cp for cp in settings.TEMPLATES[0]['OPTIONS']['context_processors']]
        if 'core.context_processors.cookie_preferences' in context_processors:
            self.stdout.write(self.style.SUCCESS('✅ cookie_preferences context processor registrado'))
        else:
            self.stdout.write(self.style.ERROR('❌ cookie_preferences context processor no registrado'))

        # 8. Resumen final
        self.stdout.write('\n📊 Resumen de la prueba:')
        self.stdout.write('=' * 50)
        self.stdout.write(f'✅ Usuario de prueba: {username}')
        self.stdout.write(f'✅ Login: {"Exitoso" if login_success else "Fallido"}')
        self.stdout.write(f'✅ Preferencias configuradas: {len(settings.CUSTOM_COOKIES)} tipos')
        self.stdout.write(f'✅ Temas disponibles: {len(settings.ALLOWED_THEMES)} opciones')
        self.stdout.write(f'✅ Layouts disponibles: {len(settings.ALLOWED_LAYOUTS)} opciones')
        
        self.stdout.write('\n🎉 ¡Prueba del sistema de cookies completada!')
        self.stdout.write('\n💡 Para probar manualmente:')
        self.stdout.write('   1. Inicia sesión en la plataforma')
        self.stdout.write('   2. Haz clic en el botón de engranaje (⚙️) en el header')
        self.stdout.write('   3. Cambia las preferencias y guarda')
        self.stdout.write('   4. Verifica que los cambios se aplican inmediatamente') 