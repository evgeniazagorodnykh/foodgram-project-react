from django.contrib import admin

from .models import Recipe, Ingredient, Tag, Favorite


class RecipeAdmin(admin.ModelAdmin):
    """Регистрация модели `Recipe` для админки."""
    list_display = (
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
        'favorite_count'
    )
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('tags', 'ingredients')

    def favorite_count(self, obj):
        return Favorite.objects.filter(recipe_id=obj.id).count()


class IngredientAdmin(admin.ModelAdmin):
    """Регистрация модели `Tag` для админки."""
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Регистрация модели `Tag` для админки."""
    list_display = (
        'id',
        'name',
        'color',
        'slug',
    )


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
