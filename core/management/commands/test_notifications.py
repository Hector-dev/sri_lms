from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import MicroCourse, Lesson
from core.models import Notification
from django.utils import timezone

class Command(BaseCommand):
    help = 'Prueba el sistema de notificaciones creando notificaciones de ejemplo'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Obtener usuarios existentes
        try:
            instructor = User.objects.get(username='instructor_demo')
            student = User.objects.get(username='estudiante_demo')
            course = MicroCourse.objects.first()
            
            self.stdout.write('Creando notificaciones de prueba...')
            
            # Notificaciones para el instructor
            Notification.objects.create(
                user=instructor,
                message=f'El estudiante {student.username} se ha inscrito en tu curso "{course.title}".'
            )
            
            Notification.objects.create(
                user=instructor,
                message=f'El estudiante {student.username} ha completado la lección "Introducción" de tu curso "{course.title}".'
            )
            
            Notification.objects.create(
                user=instructor,
                message=f'El estudiante {student.username} ha completado el test "Test de Ejemplo" con una puntuación de 85% (17/20 correctas).'
            )
            
            # Notificaciones para el estudiante
            Notification.objects.create(
                user=student,
                message=f'Te has inscrito exitosamente en el curso "{course.title}". ¡Bienvenido!'
            )
            
            Notification.objects.create(
                user=student,
                message=f'¡Felicidades! Has completado la lección "Introducción" del curso "{course.title}".'
            )
            
            Notification.objects.create(
                user=student,
                message=f'Has completado el test "Test de Ejemplo" del curso "{course.title}" con una puntuación de 85% (17/20 correctas).'
            )
            
            # Notificación de bienvenida
            Notification.objects.create(
                user=student,
                message='¡Bienvenido a SRI Learning! Tu cuenta ha sido creada exitosamente.'
            )
            
            self.stdout.write(self.style.SUCCESS(f'Se crearon 7 notificaciones de prueba:'))
            self.stdout.write(f'  - 4 notificaciones para el instructor')
            self.stdout.write(f'  - 3 notificaciones para el estudiante')
            self.stdout.write(f'  - 1 notificación de bienvenida')
            
            # Mostrar estadísticas
            instructor_notifications = Notification.objects.filter(user=instructor, read=False).count()
            student_notifications = Notification.objects.filter(user=student, read=False).count()
            
            self.stdout.write(f'\nNotificaciones sin leer:')
            self.stdout.write(f'  - Instructor: {instructor_notifications}')
            self.stdout.write(f'  - Estudiante: {student_notifications}')
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontraron usuarios de prueba. Ejecuta primero: python manage.py seed_sample_data'))
        except MicroCourse.DoesNotExist:
            self.stdout.write(self.style.ERROR('No se encontraron cursos. Ejecuta primero: python manage.py seed_sample_data')) 