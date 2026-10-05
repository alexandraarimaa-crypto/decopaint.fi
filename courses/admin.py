from django.contrib import admin
from .models import Course, CourseRegistration, CourseRegistrationFile, CourseAdditionalImage

class CourseRegistrationFileInline(admin.TabularInline):
    model = CourseRegistrationFile
    extra = 0

class CourseAdditionalImageInline(admin.TabularInline):
    model = CourseAdditionalImage
    extra = 1

@admin.register(CourseRegistration)
class CourseRegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'email', 'created_at')
    list_filter = ('course', 'created_at')
    inlines = [CourseRegistrationFileInline]
    readonly_fields = ('created_at',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    filter_horizontal = ('categories',)
    inlines = [CourseAdditionalImageInline]
