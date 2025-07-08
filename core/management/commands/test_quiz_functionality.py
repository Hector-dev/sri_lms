from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import MicroCourse, Test, Question
from django.utils import timezone

class Command(BaseCommand):
    help = 'Prueba la funcionalidad de quizzes/tests creando tests de ejemplo'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        try:
            # Obtener instructor y curso existentes
            instructor = User.objects.get(username='instructor_demo')
            course = MicroCourse.objects.first()
            
            if not course:
                self.stdout.write(self.style.ERROR('No se encontró ningún curso. Ejecuta primero: python manage.py seed_sample_data'))
                return
            
            self.stdout.write('Creando tests de ejemplo...')
            
            # Crear primer test
            test1 = Test.objects.create(
                course=course,
                title='Test de Introducción',
                description='Test básico para evaluar los conocimientos iniciales del curso.',
                order=1,
                max_attempts=2,
                time_limit=15
            )
            
            # Crear preguntas para el primer test
            questions1 = [
                {
                    'text': '¿Cuál es el propósito principal de este curso?',
                    'option_a': 'Aprender programación básica',
                    'option_b': 'Mejorar habilidades de diseño',
                    'option_c': 'Estudiar matemáticas avanzadas',
                    'option_d': 'Aprender idiomas extranjeros',
                    'correct_option': 'A'
                },
                {
                    'text': '¿Qué nivel de experiencia se requiere para este curso?',
                    'option_a': 'Experto',
                    'option_b': 'Intermedio',
                    'option_c': 'Principiante',
                    'option_d': 'Avanzado',
                    'correct_option': 'C'
                },
                {
                    'text': '¿Cuántas lecciones incluye este curso?',
                    'option_a': '5 lecciones',
                    'option_b': '10 lecciones',
                    'option_c': '15 lecciones',
                    'option_d': '20 lecciones',
                    'correct_option': 'B'
                }
            ]
            
            for q_data in questions1:
                Question.objects.create(test=test1, **q_data)
            
            # Crear segundo test
            test2 = Test.objects.create(
                course=course,
                title='Test de Evaluación Final',
                description='Test final para evaluar la comprensión completa del curso.',
                order=2,
                max_attempts=1,
                time_limit=30
            )
            
            # Crear preguntas para el segundo test
            questions2 = [
                {
                    'text': '¿Cuál es la mejor práctica para aprender en este curso?',
                    'option_a': 'Solo ver los videos',
                    'option_b': 'Practicar regularmente y hacer los ejercicios',
                    'option_c': 'Memorizar todo el contenido',
                    'option_d': 'Saltarse las lecciones difíciles',
                    'correct_option': 'B'
                },
                {
                    'text': '¿Qué debes hacer si tienes dudas sobre el contenido?',
                    'option_a': 'Ignorar las dudas',
                    'option_b': 'Contactar al instructor',
                    'option_c': 'Dejar el curso',
                    'option_d': 'Copiar de otros estudiantes',
                    'correct_option': 'B'
                },
                {
                    'text': '¿Cuál es el objetivo principal de los tests en este curso?',
                    'option_a': 'Hacer el curso más difícil',
                    'option_b': 'Evaluar tu comprensión del contenido',
                    'option_c': 'Perder tiempo',
                    'option_d': 'No tienen propósito',
                    'correct_option': 'B'
                },
                {
                    'text': '¿Qué pasa si no apruebas un test en el primer intento?',
                    'option_a': 'Te expulsan del curso',
                    'option_b': 'Puedes intentarlo de nuevo según el límite establecido',
                    'option_c': 'Pierdes todo el progreso',
                    'option_d': 'Nada, los tests son opcionales',
                    'correct_option': 'B'
                }
            ]
            
            for q_data in questions2:
                Question.objects.create(test=test2, **q_data)
            
            self.stdout.write(self.style.SUCCESS(f'Se crearon 2 tests de ejemplo:'))
            self.stdout.write(f'  - Test 1: "{test1.title}" (Orden: {test1.order}) - {test1.questions.count()} preguntas')
            self.stdout.write(f'  - Test 2: "{test2.title}" (Orden: {test2.order}) - {test2.questions.count()} preguntas')
            
            # Mostrar estadísticas
            total_tests = Test.objects.filter(course=course).count()
            total_questions = Question.objects.filter(test__course=course).count()
            
            self.stdout.write(f'\nEstadísticas del curso "{course.title}":')
            self.stdout.write(f'  - Total de tests: {total_tests}')
            self.stdout.write(f'  - Total de preguntas: {total_questions}')
            self.stdout.write(f'  - Lecciones: {course.lessons.count()}')
            
            self.stdout.write(f'\nPara probar la funcionalidad:')
            self.stdout.write(f'  1. Ve al curso: http://localhost:8000/courses/{course.slug}/')
            self.stdout.write(f'  2. Como instructor, verás botones para editar/eliminar tests')
            self.stdout.write(f'  3. Como estudiante, podrás realizar los tests')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontraron usuarios de prueba. Ejecuta primero: python manage.py seed_sample_data'))
        except MicroCourse.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontraron cursos. Ejecuta primero: python manage.py seed_sample_data')) 