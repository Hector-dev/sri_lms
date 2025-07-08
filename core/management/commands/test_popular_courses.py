from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import MicroCourse
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Prueba la funcionalidad de cursos populares'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Crear algunos estudiantes adicionales para probar
        students = []
        for i in range(1, 6):
            student, created = User.objects.get_or_create(
                username=f'estudiante_test_{i}',
                defaults={
                    'email': f'estudiante{i}@test.com',
                    'user_type': 'student'
                }
            )
            if created:
                student.set_password('test1234')
                student.save()
                self.stdout.write(f'Creado estudiante: {student.username}')
            students.append(student)
        
        # Obtener el curso existente
        course = MicroCourse.objects.first()
        if course:
            # Inscribir estudiantes en el curso
            for student in students:
                course.students.add(student)
                self.stdout.write(f'Inscrito {student.username} en {course.title}')
            
            # Mostrar estadísticas
            self.stdout.write(f'\nEstadísticas del curso "{course.title}":')
            self.stdout.write(f'Total de estudiantes: {course.students.count()}')
            
            # Mostrar estudiantes recientes (último mes)
            one_month_ago = timezone.now() - timedelta(days=30)
            recent_students = course.students.filter(date_joined__gte=one_month_ago)
            self.stdout.write(f'Estudiantes del último mes: {recent_students.count()}')
            
            # Listar estudiantes recientes
            if recent_students.exists():
                self.stdout.write('Estudiantes recientes:')
                for student in recent_students:
                    self.stdout.write(f'  - {student.username} (registrado: {student.date_joined.strftime("%d/%m/%Y")})')
            
        else:
            self.stdout.write('No hay cursos disponibles para probar.')
        
        self.stdout.write(self.style.SUCCESS('Prueba completada exitosamente')) 