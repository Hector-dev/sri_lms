from django.shortcuts import render
from courses.models import MicroCourse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Create your views here.

def index(request):
    # Calcular la fecha de hace un mes
    one_month_ago = timezone.now() - timedelta(days=30)
    
    # Obtener cursos con más estudiantes en el último mes
    # Usamos la tabla intermedia para filtrar por fecha de inscripción
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Obtener usuarios que se registraron en el último mes
    recent_users = User.objects.filter(
        date_joined__gte=one_month_ago,
        user_type='student'
    )
    
    # Obtener cursos con más estudiantes recientes
    popular_courses = MicroCourse.objects.annotate(
        recent_student_count=Count('students', filter=Q(students__in=recent_users))
    ).filter(
        recent_student_count__gt=0
    ).order_by('-recent_student_count', '-created_at')[:5]
    
    # Si no hay cursos con estudiantes recientes, mostrar por orden de creación
    if not popular_courses.exists():
        popular_courses = MicroCourse.objects.annotate(
            total_student_count=Count('students')
        ).order_by('-created_at')[:5]
    
    context = {'featured_courses': popular_courses}
    if request.user.is_authenticated:
        from core.models import Notification
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'index.html', context)
