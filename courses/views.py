from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from .models import MicroCourse, Lesson, Test, Question, TestResult, TestAnswer, CourseMaterial, LessonProgress
from .forms import MicroCourseForm, LessonFormSet, TestForm, QuestionFormSet, CourseMaterialForm
from django.views.decorators.http import require_POST
from django import forms
from django.forms import modelformset_factory
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from core.models import Notification
from django.conf import settings
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

# Create your views here.

class CourseListView(ListView):
    model = MicroCourse
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = MicroCourse.objects.select_related('instructor').prefetch_related('lessons')
        
        # Filtro de búsqueda por texto
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                models.Q(title__icontains=query) |
                models.Q(short_description__icontains=query) |
                models.Q(instructor__username__icontains=query) |
                models.Q(instructor__first_name__icontains=query) |
                models.Q(instructor__last_name__icontains=query)
            )
        
        # Filtro por categoría
        category = self.request.GET.get('category', '').strip()
        if category:
            queryset = queryset.filter(category=category)
        
        # Filtro por dificultad
        difficulty = self.request.GET.get('difficulty', '').strip()
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filtro por duración/tipo
        duration = self.request.GET.get('duration', '').strip()
        if duration:
            if duration == 'microcurso':
                queryset = queryset.filter(lessons__isnull=True)
            elif duration == 'corto':
                queryset = queryset.annotate(lesson_count=Count('lessons')).filter(lesson_count__lte=3, lesson_count__gt=0)
            elif duration == 'medio':
                queryset = queryset.annotate(lesson_count=Count('lessons')).filter(lesson_count__lte=7, lesson_count__gt=3)
            elif duration == 'largo':
                queryset = queryset.annotate(lesson_count=Count('lessons')).filter(lesson_count__gt=7)
        
        # Ordenamiento
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by == 'title':
            queryset = queryset.order_by('title')
        elif order_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif order_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif order_by == 'popular':
            queryset = queryset.annotate(student_count=Count('students')).order_by('-student_count')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_difficulty'] = self.request.GET.get('difficulty', '')
        context['selected_duration'] = self.request.GET.get('duration', '')
        context['selected_order'] = self.request.GET.get('order_by', '-created_at')
        
        # Opciones para los filtros
        context['categories'] = MicroCourse.CATEGORY_CHOICES
        context['difficulties'] = MicroCourse.DIFFICULTY_CHOICES
        context['durations'] = [
            ('microcurso', 'Microcurso (solo video promo)'),
            ('corto', 'Corto (1-3 lecciones)'),
            ('medio', 'Medio (4-7 lecciones)'),
            ('largo', 'Largo (8+ lecciones)'),
        ]
        context['order_options'] = [
            ('-created_at', 'Más recientes'),
            ('created_at', 'Más antiguos'),
            ('title', 'Alfabético'),
            ('popular', 'Más populares'),
        ]
        
        return context

class CourseDetailView(DetailView):
    model = MicroCourse
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all()
        context['students'] = self.object.students.all()
        return context

def search_courses(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    try:
        # Búsqueda más amplia: título, descripción e instructor
        results = MicroCourse.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(short_description__icontains=query) |
            models.Q(instructor__username__icontains=query) |
            models.Q(instructor__first_name__icontains=query) |
            models.Q(instructor__last_name__icontains=query)
        ).select_related('instructor')[:10]  # Aumentar límite a 10
        
        data = [{
            'id': course.id, 
            'title': course.title, 
            'slug': course.slug,
            'instructor': course.instructor.get_full_name() or course.instructor.username,
            'description': course.short_description[:100] + '...' if len(course.short_description) > 100 else course.short_description
        } for course in results]
        return JsonResponse({'results': data})
    except Exception as e:
        logging.error(f"Error en búsqueda de cursos: {e}")
        return JsonResponse({'results': [], 'error': 'Error en la búsqueda'})

# Vistas para instructores
@login_required
def create_course(request):
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden crear cursos.")
        return redirect('home')
    
    MaterialFormSet = modelformset_factory(CourseMaterial, form=CourseMaterialForm, extra=1, can_delete=True)
    
    if request.method == 'POST':
        logger = logging.getLogger('django')
        logger.warning('Se presionó Guardar Curso (POST en create_course) por el usuario: %s', request.user)
        
        form = MicroCourseForm(request.POST, request.FILES)
        formset = LessonFormSet(request.POST)
        test_form = TestForm(request.POST, prefix='test')
        question_formset = QuestionFormSet(request.POST, prefix='question')
        material_formset = MaterialFormSet(request.POST, request.FILES, queryset=CourseMaterial.objects.none())
        
        # Validar todos los formularios
        forms_valid = (
            form.is_valid() and 
            formset.is_valid() and 
            test_form.is_valid() and 
            question_formset.is_valid() and 
            material_formset.is_valid()
        )
        
        if forms_valid:
            try:
                # Crear el curso
                course = form.save(commit=False)
                course.instructor = request.user
                course.save()
                
                # Guardar lecciones
                formset.instance = course
                formset.save()
                
                # Guardar test y preguntas si se proporcionaron
                if test_form.cleaned_data.get('title'):
                    test = test_form.save(commit=False)
                    test.course = course
                    test.save()
                    question_formset.instance = test
                    question_formset.save()
                
                # Guardar materiales
                for material_form in material_formset:
                    if material_form.cleaned_data and not material_form.cleaned_data.get('DELETE'):
                        if material_form.cleaned_data.get('file') or material_form.cleaned_data.get('url'):
                            material = material_form.save(commit=False)
                            material.course = course
                            material.save()
                
                messages.success(request, f"El curso '{course.title}' ha sido creado exitosamente.")
                
                # Notificación para el instructor
                Notification.objects.create(
                    user=request.user,
                    message=f'Has creado exitosamente el curso "{course.title}". ¡Comienza a agregar contenido!'
                )
                
                return redirect('courses:instructor_dashboard')
                
            except Exception as e:
                logging.error(f"Error al crear curso: {e}")
                messages.error(request, "Error al crear el curso. Por favor, inténtalo de nuevo.")
        else:
            # Mostrar errores específicos
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en {field}: {error}")
            if not formset.is_valid():
                messages.error(request, "Error en las lecciones. Verifica que todos los campos requeridos estén completos.")
            if not test_form.is_valid() and test_form.cleaned_data.get('title'):
                messages.error(request, "Error en la configuración del test.")
            if not question_formset.is_valid() and test_form.cleaned_data.get('title'):
                messages.error(request, "Error en las preguntas del test.")
            if not material_formset.is_valid():
                messages.error(request, "Error en los materiales del curso.")
    else:
        form = MicroCourseForm()
        formset = LessonFormSet()
        test_form = TestForm(prefix='test')
        question_formset = QuestionFormSet(prefix='question')
        material_formset = MaterialFormSet(queryset=CourseMaterial.objects.none())
    
    return render(request, 'courses/course_form.html', {
        'form': form,
        'formset': formset,
        'test_form': test_form,
        'question_formset': question_formset,
        'material_formset': material_formset,
        'title': 'Crear Nuevo Curso'
    })

@login_required
def edit_course(request, pk):
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden editar cursos.")
        return redirect('home')
    course = get_object_or_404(MicroCourse, pk=pk)
    if request.user != course.instructor:
        messages.error(request, "No tienes permiso para editar este curso.")
        return redirect('courses:instructor_dashboard')
    test = course.tests.first()
    MaterialFormSet = modelformset_factory(CourseMaterial, form=CourseMaterialForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = MicroCourseForm(request.POST, request.FILES, instance=course)
        formset = LessonFormSet(request.POST, instance=course)
        test_form = TestForm(request.POST, instance=test, prefix='test')
        question_formset = QuestionFormSet(request.POST, instance=test, prefix='question')
        material_formset = MaterialFormSet(request.POST, request.FILES, queryset=CourseMaterial.objects.filter(course=course))
        if form.is_valid() and formset.is_valid() and test_form.is_valid() and question_formset.is_valid() and material_formset.is_valid():
            try:
                form.save()
                formset.save()
                if test_form.cleaned_data.get('title'):
                    test = test_form.save(commit=False)
                    test.course = course
                    test.save()
                    question_formset.instance = test
                    question_formset.save()
                for material_form in material_formset:
                    if material_form.cleaned_data and (material_form.cleaned_data.get('file') or material_form.cleaned_data.get('url')):
                        material = material_form.save(commit=False)
                        material.course = course
                        material.save()
                    elif material_form.cleaned_data.get('DELETE') and material_form.instance.pk:
                        material_form.instance.delete()
                messages.success(request, f"El curso '{course.title}' ha sido actualizado exitosamente.")
                
                # Notificación para el instructor
                Notification.objects.create(
                    user=request.user,
                    message=f'Has actualizado exitosamente el curso "{course.title}".'
                )
                
                return redirect('courses:instructor_dashboard')
            except Exception as e:
                logging.error(f"Error al editar curso: {e}")
                messages.error(request, "Error al actualizar el curso. Por favor, inténtalo de nuevo.")
    else:
        form = MicroCourseForm(instance=course)
        formset = LessonFormSet(instance=course)
        test_form = TestForm(instance=test, prefix='test')
        question_formset = QuestionFormSet(instance=test, prefix='question')
        material_formset = MaterialFormSet(queryset=CourseMaterial.objects.filter(course=course))
    return render(request, 'courses/course_form.html', {
        'form': form,
        'formset': formset,
        'test_form': test_form,
        'question_formset': question_formset,
        'material_formset': material_formset,
        'title': f'Editar Curso: {course.title}',
        'course': course
    })

@login_required
def instructor_dashboard(request):
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden acceder al panel de instructor.")
        return redirect('home')
    # Obtener los cursos del instructor con conteo de lecciones
    courses = MicroCourse.objects.filter(instructor=request.user).annotate(lesson_count=Count('lessons'))
    tests = Test.objects.filter(course__in=courses)
    test_results = TestResult.objects.filter(test__in=tests).select_related('student', 'test').order_by('student__username', 'test__title', 'taken_at')
    context = {'courses': courses, 'test_results': test_results}
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    return render(request, 'courses/instructor_dashboard.html', context)

@login_required
@require_POST
def enroll_course(request, pk):
    course = get_object_or_404(MicroCourse, pk=pk)
    # No permitir que el instructor se inscriba en su propio curso
    if request.user == course.instructor:
        messages.error(request, 'No puedes inscribirte en un curso que tú mismo creaste.')
        return redirect('courses:course_detail', slug=course.slug)
    # Permitir inscripción a estudiantes y a instructores (que no sean el creador)
    course.students.add(request.user)
    
    # Crear notificaciones
    # Notificación para el estudiante/instructor que se inscribe
    Notification.objects.create(
        user=request.user,
        message=f'Te has inscrito exitosamente en el curso "{course.title}". ¡Bienvenido!'
    )
    
    # Notificación para el instructor del curso
    if request.user != course.instructor:
        Notification.objects.create(
            user=course.instructor,
            message=f'El usuario {request.user.username} se ha inscrito en tu curso "{course.title}".'
        )
    
    messages.success(request, f'Te has inscrito en el curso "{course.title}" exitosamente.')
    return redirect('courses:course_detail', slug=course.slug)

class TestAnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)
        for q in questions:
            self.fields[f'q_{q.id}'] = forms.ChoiceField(
                label=q.text,
                choices=[('A', q.option_a), ('B', q.option_b), ('C', q.option_c), ('D', q.option_d)],
                widget=forms.RadioSelect,
                required=True
            )

@login_required
def take_test(request, course_id, test_id):
    course = get_object_or_404(MicroCourse, id=course_id)
    test = get_object_or_404(Test, id=test_id, course=course)
    
    if request.user.user_type != 'student':
        messages.error(request, 'Solo los estudiantes pueden responder tests.')
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.user not in course.students.all():
        messages.error(request, 'Debes estar inscrito en el curso para poder realizar el test.')
        return redirect('courses:course_detail', slug=course.slug)
    
    questions = test.questions.all()
    if not questions.exists():
        messages.error(request, 'Este test no tiene preguntas configuradas.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Contar intentos previos
    attempts = TestResult.objects.filter(test=test, student=request.user).count()
    if attempts >= test.max_attempts:
        messages.error(request, f'Has alcanzado el número máximo de intentos ({test.max_attempts}) para este test.')
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        form = TestAnswerForm(request.POST, questions=questions)
        if form.is_valid():
            try:
                correct = 0
                total = questions.count()
                
                # Crear el resultado del test
                result = TestResult.objects.create(
                    test=test,
                    student=request.user,
                    score=0,
                    correct=0,
                    total=total
                )
                
                # Procesar respuestas
                for q in questions:
                    answer = form.cleaned_data.get(f'q_{q.id}')
                    if answer:
                        is_correct = answer == q.correct_option
                        if is_correct:
                            correct += 1
                        TestAnswer.objects.create(
                            test_result=result,
                            question=q,
                            selected_option=answer,
                            is_correct=is_correct
                        )
                
                # Calcular puntuación
                score = int((correct / total) * 100) if total > 0 else 0
                result.score = score
                result.correct = correct
                result.save()
                
                # Crear notificaciones
                # Notificación para el estudiante
                Notification.objects.create(
                    user=request.user,
                    message=f'Has completado el test "{test.title}" del curso "{course.title}" con una puntuación de {score}% ({correct}/{total} correctas).'
                )
                
                # Notificación para el instructor
                Notification.objects.create(
                    user=course.instructor,
                    message=f'El estudiante {request.user.username} ha completado el test "{test.title}" del curso "{course.title}" con una puntuación de {score}% ({correct}/{total} correctas).'
                )
                
                messages.success(request, f'Test completado. Puntuación: {score}% ({correct}/{total} correctas)')
                return redirect('courses:test_result_detail', course_id=course.id, test_id=test.id, result_id=result.id)
                
            except Exception as e:
                logging.error(f"Error al procesar test: {e}")
                messages.error(request, "Error al procesar el test. Por favor, inténtalo de nuevo.")
    else:
        form = TestAnswerForm(questions=questions)
    
    return render(request, 'courses/take_test.html', {
        'test': test,
        'course': course,
        'form': form,
        'attempt': attempts + 1,
        'max_attempts': test.max_attempts,
        'time_limit': test.time_limit
    })

@login_required
def test_result_detail(request, course_id, test_id, result_id):
    """Vista para mostrar los resultados detallados de un test"""
    course = get_object_or_404(MicroCourse, id=course_id)
    test = get_object_or_404(Test, id=test_id, course=course)
    result = get_object_or_404(TestResult, id=result_id, test=test, student=request.user)
    
    # Verificar que el usuario tiene acceso a este resultado
    if request.user != result.student:
        messages.error(request, 'No tienes permiso para ver este resultado.')
        return redirect('courses:course_detail', slug=course.slug)
    
    # Obtener las respuestas del test
    answers = TestAnswer.objects.filter(test_result=result).select_related('question')
    
    # Contar intentos previos para este test
    attempts = TestResult.objects.filter(test=test, student=request.user).count()
    
    context = {
        'course': course,
        'test': test,
        'result': result,
        'answers': answers,
        'score': result.score,
        'correct': result.correct,
        'total': result.total,
        'attempt': attempts,
        'max_attempts': test.max_attempts,
    }
    
    return render(request, 'courses/test_result.html', context)

@login_required
@require_POST
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.user.user_type != 'student' or request.user not in lesson.course.students.all():
        return JsonResponse({'success': False, 'error': 'No autorizado'})
    try:
        # Verificar si ya está completada
        progress, created = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
        
        if created:
            # Crear notificaciones solo si es la primera vez que se completa
            # Notificación para el estudiante
            Notification.objects.create(
                user=request.user,
                message=f'¡Felicidades! Has completado la lección "{lesson.title}" del curso "{lesson.course.title}".'
            )
            
            # Notificación para el instructor
            Notification.objects.create(
                user=lesson.course.instructor,
                message=f'El estudiante {request.user.username} ha completado la lección "{lesson.title}" de tu curso "{lesson.course.title}".'
            )
        
        return JsonResponse({'success': True})
    except Exception as e:
        logging.error(f"Error al completar lección: {e}")
        return JsonResponse({'success': False, 'error': 'Error interno del servidor'})

def course_detail_with_tests(request, slug):
    course = get_object_or_404(MicroCourse, slug=slug)
    lessons = course.lessons.all()
    tests = course.tests.all()
    materials = course.materials.all()
    progress = []
    test_results = {}
    
    if request.user.is_authenticated and request.user.user_type == 'student':
        progress = list(LessonProgress.objects.filter(student=request.user, lesson__in=lessons).values_list('lesson_id', flat=True))
        # Obtener los mejores resultados de cada test para el usuario
        for test in tests:
            best_result = TestResult.objects.filter(
                test=test, 
                student=request.user
            ).order_by('-score', '-taken_at').first()
            if best_result:
                test_results[test.id] = best_result
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'tests': tests,
        'materials': materials,
        'progress': progress,
        'test_results': test_results
    })

@login_required
def download_certificate(request, course_id):
    course = get_object_or_404(MicroCourse, id=course_id)
    user = request.user
    if user.user_type != 'student' or user not in course.students.all():
        messages.error(request, 'No autorizado para descargar el certificado.')
        return redirect('courses:course_detail', slug=course.slug)
    
    try:
        lessons = course.lessons.all()
        completed_lessons = LessonProgress.objects.filter(student=user, lesson__in=lessons).count()
        if completed_lessons < lessons.count():
            messages.error(request, 'Debes completar todas las lecciones para obtener el certificado.')
            return redirect('courses:course_detail', slug=course.slug)
        
        tests = course.tests.all()
        passed = False
        for test in tests:
            if TestResult.objects.filter(test=test, student=user, score__gte=60).exists():
                passed = True
                break
        if not passed:
            messages.error(request, 'Debes aprobar al menos un test del curso para obtener el certificado.')
            return redirect('courses:course_detail', slug=course.slug)
        
        # Obtener la fecha de finalización más reciente
        try:
            latest_progress = user.lesson_progress.filter(lesson__course=course).latest("completed_at")
            completion_date = latest_progress.completed_at.strftime("%d/%m/%Y")
        except ObjectDoesNotExist:
            completion_date = "Fecha no disponible"
        
        # Generar PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont('Helvetica-Bold', 20)
        p.drawCentredString(300, 700, 'Certificado de Finalización')
        p.setFont('Helvetica', 14)
        p.drawCentredString(300, 650, f'Este certificado se otorga a:')
        p.setFont('Helvetica-Bold', 16)
        p.drawCentredString(300, 620, user.get_full_name() or user.username)
        p.setFont('Helvetica', 14)
        p.drawCentredString(300, 580, f'Por completar el curso:')
        p.setFont('Helvetica-Bold', 16)
        p.drawCentredString(300, 550, course.title)
        p.setFont('Helvetica', 12)
        p.drawCentredString(300, 500, f'Instructor: {course.instructor.get_full_name() or course.instructor.username}')
        p.drawCentredString(300, 480, f'Fecha: {completion_date}')
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=certificado_{course.slug}_{user.username}.pdf'
        
        # Notificación para el estudiante
        Notification.objects.create(
            user=user,
            message=f'¡Felicidades! Has completado el curso "{course.title}" y descargado tu certificado.'
        )
        # Notificación para el instructor
        Notification.objects.create(
            user=course.instructor,
            message=f'El estudiante {user.username} ha completado el curso "{course.title}".'
        )
        return response
        
    except Exception as e:
        logging.error(f"Error al generar certificado: {e}")
        messages.error(request, 'Error al generar el certificado. Por favor, inténtalo de nuevo.')
        return redirect('courses:course_detail', slug=course.slug)

@login_required
def manage_attempts(request, course_id):
    course = get_object_or_404(MicroCourse, id=course_id)
    if request.user != course.instructor:
        messages.error(request, 'No autorizado.')
        return redirect('courses:instructor_dashboard')
    tests = course.tests.all()
    results = TestResult.objects.filter(test__in=tests).select_related('student', 'test').order_by('student__username', 'test__title', 'taken_at')
    if request.method == 'POST':
        result_id = request.POST.get('result_id')
        if result_id:
            try:
                result = get_object_or_404(TestResult, id=result_id, test__in=tests)
                result.delete()
                messages.success(request, 'Intento eliminado correctamente.')
            except Exception as e:
                logging.error(f"Error al eliminar intento: {e}")
                messages.error(request, 'Error al eliminar el intento.')
            return redirect('courses:manage_attempts', course_id=course.id)
    return render(request, 'courses/manage_attempts.html', {'course': course, 'results': results})

@login_required
def create_test(request, course_id):
    """Vista para crear un nuevo test en un curso"""
    course = get_object_or_404(MicroCourse, id=course_id)
    
    # Verificar permisos
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden crear tests.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.user != course.instructor:
        messages.error(request, "No tienes permiso para crear tests en este curso.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        test_form = TestForm(request.POST, course=course)
        question_formset = QuestionFormSet(request.POST, prefix='question')
        
        if test_form.is_valid() and question_formset.is_valid():
            try:
                # Crear el test
                test = test_form.save(commit=False)
                test.course = course
                test.save()
                
                # Guardar las preguntas
                question_formset.instance = test
                question_formset.save()
                
                # Crear notificación
                Notification.objects.create(
                    user=request.user,
                    message=f'Has creado exitosamente el test "{test.title}" en el curso "{course.title}".'
                )
                
                messages.success(request, f'Test "{test.title}" creado exitosamente.')
                return redirect('courses:course_detail', slug=course.slug)
                
            except Exception as e:
                logging.error(f"Error al crear test: {e}")
                messages.error(request, "Error al crear el test. Por favor, inténtalo de nuevo.")
        else:
            if not test_form.is_valid():
                for field, errors in test_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en {field}: {error}")
            if not question_formset.is_valid():
                messages.error(request, "Error en las preguntas del test.")
    else:
        test_form = TestForm(course=course)
        question_formset = QuestionFormSet(prefix='question')
    
    context = {
        'test_form': test_form,
        'question_formset': question_formset,
        'course': course,
        'title': f'Añadir Test - {course.title}'
    }
    
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    
    return render(request, 'courses/test_form.html', context)

@login_required
def edit_test(request, course_id, test_id):
    """Vista para editar un test existente"""
    course = get_object_or_404(MicroCourse, id=course_id)
    test = get_object_or_404(Test, id=test_id, course=course)
    
    # Verificar permisos
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden editar tests.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.user != course.instructor:
        messages.error(request, "No tienes permiso para editar este test.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        test_form = TestForm(request.POST, instance=test, course=course)
        question_formset = QuestionFormSet(request.POST, instance=test, prefix='question')
        
        if test_form.is_valid() and question_formset.is_valid():
            try:
                # Guardar el test
                test_form.save()
                
                # Guardar las preguntas
                question_formset.save()
                
                # Crear notificación
                Notification.objects.create(
                    user=request.user,
                    message=f'Has actualizado exitosamente el test "{test.title}" en el curso "{course.title}".'
                )
                
                messages.success(request, f'Test "{test.title}" actualizado exitosamente.')
                return redirect('courses:course_detail', slug=course.slug)
                
            except Exception as e:
                logging.error(f"Error al editar test: {e}")
                messages.error(request, "Error al actualizar el test. Por favor, inténtalo de nuevo.")
        else:
            if not test_form.is_valid():
                for field, errors in test_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error en {field}: {error}")
            if not question_formset.is_valid():
                messages.error(request, "Error en las preguntas del test.")
    else:
        test_form = TestForm(instance=test, course=course)
        question_formset = QuestionFormSet(instance=test, prefix='question')
    
    context = {
        'test_form': test_form,
        'question_formset': question_formset,
        'course': course,
        'test': test,
        'title': f'Editar Test - {test.title}'
    }
    
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    
    return render(request, 'courses/test_form.html', context)

@login_required
def delete_test(request, course_id, test_id):
    """Vista para eliminar un test"""
    course = get_object_or_404(MicroCourse, id=course_id)
    test = get_object_or_404(Test, id=test_id, course=course)
    
    # Verificar permisos
    if request.user.user_type != 'instructor':
        messages.error(request, "Solo los instructores pueden eliminar tests.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.user != course.instructor:
        messages.error(request, "No tienes permiso para eliminar este test.")
        return redirect('courses:course_detail', slug=course.slug)
    
    if request.method == 'POST':
        try:
            test_title = test.title
            test.delete()
            
            # Crear notificación
            Notification.objects.create(
                user=request.user,
                message=f'Has eliminado el test "{test_title}" del curso "{course.title}".'
            )
            
            messages.success(request, f'Test "{test_title}" eliminado exitosamente.')
            return redirect('courses:course_detail', slug=course.slug)
            
        except Exception as e:
            logging.error(f"Error al eliminar test: {e}")
            messages.error(request, "Error al eliminar el test. Por favor, inténtalo de nuevo.")
    
    context = {
        'course': course,
        'test': test,
        'title': f'Eliminar Test - {test.title}'
    }
    
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(user=request.user, read=False)
    
    return render(request, 'courses/delete_test.html', context)
