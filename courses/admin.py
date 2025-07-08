from django.contrib import admin
from .models import MicroCourse, Lesson

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(MicroCourse)
class MicroCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'created_at', 'featured')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('featured', 'created_at')
    search_fields = ('title', 'instructor__username')
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
