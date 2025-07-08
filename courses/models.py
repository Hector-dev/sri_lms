from django.db import models
from users.models import CustomUser
from django.utils.text import slugify
import re
from urllib.parse import urlparse
from django.core.exceptions import ValidationError
from django.conf import settings
import os

def validate_file_size(value):
    """Validar tamaño de archivo (máximo 10MB)"""
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB
        raise ValidationError("El archivo no puede ser mayor a 10MB.")

def validate_image_file(value):
    """Validar tipo de archivo de imagen"""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp).')

def validate_document_file(value):
    """Validar tipo de archivo de documento"""
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Solo se permiten archivos de documento (pdf, doc, docx, xls, xlsx, txt, csv).')

class MicroCourse(models.Model):
    CATEGORY_CHOICES = [
        ('programming', 'Programación'),
        ('design', 'Diseño'),
        ('business', 'Negocios'),
        ('marketing', 'Marketing'),
        ('languages', 'Idiomas'),
        ('music', 'Música'),
        ('cooking', 'Cocina'),
        ('fitness', 'Fitness'),
        ('photography', 'Fotografía'),
        ('writing', 'Escritura'),
        ('other', 'Otros'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    short_description = models.TextField(max_length=160)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    thumbnail = models.ImageField(
        upload_to='course_thumbnails/', 
        blank=True, 
        null=True,
        validators=[validate_file_size, validate_image_file]
    )
    promo_video_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    featured = models.BooleanField(default=False)
    students = models.ManyToManyField('users.CustomUser', related_name='enrolled_courses', blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            # Verificar si el slug ya existe y generar uno único
            while MicroCourse.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.title
    
    def get_embed_url(self):
        """Convierte la URL del video a una URL de embedding segura"""
        url = self.promo_video_url
        
        # Si no hay URL, devolver una URL por defecto o vacío
        if not url:
            return ""
        
        try:
            # Validar que sea una URL válida
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ""
                
            # YouTube
            youtube_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
            youtube_match = re.match(youtube_pattern, url)
            if youtube_match:
                video_id = youtube_match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"
            
            # Vimeo
            vimeo_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/)(\d+)'
            vimeo_match = re.match(vimeo_pattern, url)
            if vimeo_match:
                video_id = vimeo_match.group(1)
                return f"https://player.vimeo.com/video/{video_id}"
                
            # Si no coincide con ninguna plataforma conocida, devolver la URL original
            return url
            
        except Exception:
            # En caso de error en el parsing, devolver URL vacía
            return ""
    
    def get_duration(self):
        """Calcula la duración estimada del curso basada en el número de lecciones"""
        lesson_count = self.lessons.count()
        if lesson_count == 0:
            return "Microcurso (solo video promo)"
        elif lesson_count <= 3:
            return "Corto (1-3 lecciones)"
        elif lesson_count <= 7:
            return "Medio (4-7 lecciones)"
        else:
            return "Largo (8+ lecciones)"
    
    def get_course_type(self):
        """Determina si es un curso completo o microcurso"""
        if self.lessons.count() == 0:
            return "microcurso"
        return "curso"

class Lesson(models.Model):
    course = models.ForeignKey(MicroCourse, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"
        
    def get_embed_url(self):
        """Convierte la URL del video a una URL de embedding segura"""
        url = self.video_url
        
        # Si no hay URL, devolver una URL por defecto o vacío
        if not url:
            return ""
        
        try:
            # Validar que sea una URL válida
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ""
                
            # YouTube
            youtube_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
            youtube_match = re.match(youtube_pattern, url)
            if youtube_match:
                video_id = youtube_match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"
            
            # Vimeo
            vimeo_pattern = r'(?:https?:\/\/)?(?:www\.)?(?:vimeo\.com\/)(\d+)'
            vimeo_match = re.match(vimeo_pattern, url)
            if vimeo_match:
                video_id = vimeo_match.group(1)
                return f"https://player.vimeo.com/video/{video_id}"
                
            # Si no coincide con ninguna plataforma conocida, devolver la URL original
            return url
            
        except Exception:
            # En caso de error en el parsing, devolver URL vacía
            return ""

class Test(models.Model):
    course = models.ForeignKey(MicroCourse, on_delete=models.CASCADE, related_name='tests')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(help_text='Orden en el que aparece el test en el curso')
    max_attempts = models.PositiveIntegerField(default=1, help_text='Número máximo de intentos permitidos para los estudiantes')
    time_limit = models.PositiveIntegerField(default=0, help_text='Tiempo límite en minutos (0 = sin límite)')

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])

    def __str__(self):
        return f"{self.text} ({self.test.title})"

class TestResult(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='test_results')
    score = models.IntegerField()
    correct = models.IntegerField()
    total = models.IntegerField()
    taken_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.score}%)"

class TestAnswer(models.Model):
    test_result = models.ForeignKey(TestResult, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    is_correct = models.BooleanField()

    def __str__(self):
        return f"{self.question.text[:30]}... - {self.selected_option} ({'Correcta' if self.is_correct else 'Incorrecta'})"

class CourseMaterial(models.Model):
    course = models.ForeignKey(MicroCourse, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='course_materials/', 
        blank=True, 
        null=True,
        validators=[validate_file_size, validate_document_file]
    )
    url = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """Validar que se proporcione al menos un archivo o URL"""
        if not self.file and not self.url:
            raise ValidationError('Debe proporcionar un archivo o una URL.')

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class LessonProgress(models.Model):
    student = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"
