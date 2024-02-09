import django_filters

from recipe.models import Recipe, Favorite, Shopping


class ModelFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
    )
    is_favorited = django_filters.NumberFilter(
        field_name='favorites',
        method='filter_favorites'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name='shoppings',
        method='filter_shoppings'
    )

    def filter_favorites(self, queryset, name, value):
        boolean = {0: False, 1: True}
        list_recipes = []
        user = self.request.user
        for recipe in queryset:
            if Favorite.objects.filter(
                user=user,
                recipe=recipe,
            ).exists() == boolean[value]:
                list_recipes.append(recipe.id)
        return queryset.filter(id__in=list_recipes)

    def filter_shoppings(self, queryset, name, value):
        boolean = {0: False, 1: True}
        list_recipes = []
        user = self.request.user
        for recipe in queryset:
            if Shopping.objects.filter(
                user=user,
                recipe=recipe,
            ).exists() == boolean[value]:
                list_recipes.append(recipe.id)
        return queryset.filter(id__in=list_recipes)

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
