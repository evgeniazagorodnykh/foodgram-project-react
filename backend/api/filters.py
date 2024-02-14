import django_filters

from recipe.models import Recipe, Favorite, Shopping


class ModelFilter(django_filters.FilterSet):
    """Фильтр модели `Recipe`."""
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
        user = self.request.user
        if value == 1:
            return queryset.filter(id__in=Favorite.objects.filter(
                user=user
            ).values_list('recipe', flat=True))
        return queryset

    def filter_shoppings(self, queryset, name, value):
        user = self.request.user
        if value == 1:
            return queryset.filter(id__in=Shopping.objects.filter(
                user=user
            ).values_list('recipe', flat=True))
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
