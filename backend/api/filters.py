import django_filters

#from rest_framework import filters

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
        method='filter_boolean'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name='shoppings',
        method='filter_boolean'
    )

    def filter_boolean(self, queryset, name, value):
        boolean = {0: False, 1: True}
        model = {'favorites': Favorite, 'shoppings': Shopping}
        list_recipes = []
        for recipe in queryset:
            if model[name].objects.filter(
                recipe=recipe
            ).exists() == boolean[value]:
                list_recipes.append(recipe.id)
        return queryset.filter(id__in=list_recipes)

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')


# class CustomSearchFilter(filters.SearchFilter):
#     search_param = 'name'
