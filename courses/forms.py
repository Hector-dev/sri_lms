from django import forms
from .models import MicroCourse, Lesson, Test, Question, CourseMaterial
from django.db import models

class MicroCourseForm(forms.ModelForm):
    class Meta:
        model = MicroCourse
        fields = ['title', 'short_description', 'category', 'difficulty', 'thumbnail', 'promo_video_url']
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases de Bootstrap a los campos
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'video_url', 'order', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases de Bootstrap a los campos
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})

# Formset para gestionar múltiples lecciones
LessonFormSet = forms.inlineformset_factory(
    MicroCourse, 
    Lesson, 
    form=LessonForm, 
    extra=1, 
    can_delete=True
)

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'order', 'max_attempts', 'time_limit']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 1}),
            'max_attempts': forms.NumberInput(attrs={'min': 1, 'max': 10}),
            'time_limit': forms.NumberInput(attrs={'min': 0, 'max': 180}),
        }
        help_texts = {
            'order': 'Orden en el que aparece el test en el curso (1 = primero)',
            'max_attempts': 'Número máximo de intentos permitidos (1-10)',
            'time_limit': 'Tiempo límite en minutos (0 = sin límite, máximo 180)',
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # Aplicar clases de Bootstrap a los campos
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})
        
        # Si se proporciona un curso, establecer el siguiente orden disponible
        if course and not self.instance.pk:
            max_order = Test.objects.filter(course=course).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.fields['order'].initial = max_order + 1

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }

QuestionFormSet = forms.inlineformset_factory(
    Test,
    Question,
    form=QuestionForm,
    extra=1,
    can_delete=True
)

class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ['title', 'file', 'url'] 