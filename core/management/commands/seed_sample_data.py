from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import MicroCourse, Lesson, Test, Question, CourseMaterial
from core.models import Notification

class Command(BaseCommand):
    help = 'Crea datos de muestra para desarrollo y pruebas.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # Crear usuarios
        instructor, created = User.objects.get_or_create(
            username='instructor_demo', defaults={
                'email': 'instructor@example.com',
                'user_type': 'instructor'
            })
        if created:
            instructor.set_password('demo1234')
            instructor.save()
        student, created = User.objects.get_or_create(
            username='estudiante_demo', defaults={
                'email': 'estudiante@example.com',
                'user_type': 'student'
            })
        if created:
            student.set_password('demo1234')
            student.save()
        # Crear curso
        course, _ = MicroCourse.objects.get_or_create(
            title='Curso de Prueba',
            defaults={
                'slug': 'curso-de-prueba',
                'instructor': instructor,
                'short_description': 'Un curso de ejemplo para pruebas.',
                'featured': True
            })
        # Crear lección
        lesson, _ = Lesson.objects.get_or_create(
            course=course,
            order=1,
            defaults={
                'title': 'Lección de Ejemplo',
                'content': 'Contenido de la lección de ejemplo.'
            })
        # Crear test
        test, _ = Test.objects.get_or_create(
            course=course,
            defaults={
                'title': 'Test de Ejemplo',
                'description': 'Test de muestra',
                'max_attempts': 3
            })
        # Crear pregunta
        Question.objects.get_or_create(
            test=test,
            text='¿Cuál es la capital de Francia?',
            defaults={
                'option_a': 'Madrid',
                'option_b': 'París',
                'option_c': 'Berlín',
                'option_d': 'Roma',
                'correct_option': 'B'
            })
        # Crear material
        CourseMaterial.objects.get_or_create(
            course=course,
            title='Material de Ejemplo',
            defaults={'url': 'https://www.example.com'}
        )
        # Inscribir estudiante
        course.students.add(student)
        # Notificaciones
        Notification.objects.get_or_create(user=student, message='¡Bienvenido al curso de prueba!')
        Notification.objects.get_or_create(user=instructor, message='Has creado un curso de prueba.')
        # Guardar credenciales en txt
        with open('usuarios_demo.txt', 'w') as f:
            f.write('Usuarios de muestra:\n')
            f.write('Instructor: usuario: instructor_demo, contraseña: demo1234\n')
            f.write('Estudiante: usuario: estudiante_demo, contraseña: demo1234\n')
        self.stdout.write(self.style.SUCCESS('Datos de muestra creados. Credenciales en usuarios_demo.txt')) 