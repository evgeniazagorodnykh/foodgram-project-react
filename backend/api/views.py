import os

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    mixins,
    filters,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from djoser.views import UserViewSet

from recipe.models import (
    Recipe,
    Ingredient,
    Tag,
    Subscription,
    Favorite,
    Shopping,
    IngredientRecipe,
)
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    IngredientSerializer,
    FavoriteSerializer,
    SubscriptionSerializer,
    ShoppingSerializer,
)
from .permissions import AuthorOrReadOnly
from .filters import ModelFilter


User = get_user_model()


class CreateDestroyViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class CustomUserViewSet(UserViewSet):
    """Обработка запросов `users`.

    Запросы к `api/users/me` доступны
    любому авторизованному пользователю.

    Запросы к `api/users/subscriptions` доступны
    любому авторизованному пользователю.
    """
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=['GET'],
        detail=False,
        url_name='subscriptions',
        url_path='subscriptions',
        permission_classes=[IsAuthenticated],
        pagination_class=CustomPagination
    )
    def get_subscription(self, request):
        limit = request.GET.get('recipes_limit', None)
        user = self.request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={
                    'recipes_limit': limit
                }
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            Subscription.objects.filter(user=user),
            many=True,
            context={
                'recipes_limit': limit
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    pagination_class = None
    filterset_fields = ('name',)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Обработка запросов `recpes`."""
    queryset = Recipe.objects.select_related(
        'author'
    ).all()
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ModelFilter
    pagination_class = CustomPagination
    ordering = ['-id']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['GET'],
        detail=False,
        url_name='download_shopping_cart',
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        shopping = Shopping.objects.filter(user=user)
        shopping_dict = {}
        path = "shopping_cart.txt"
        file = open(path, "w+")
        file.writelines('Список покупок:\n')
        for elem in shopping:
            ingredients = IngredientRecipe.objects.filter(recipe=elem.recipe)
            for ingredient in ingredients:
                name = ingredient.ingredient
                count = ingredient.amount
                if shopping_dict.get(name) is not None:
                    shopping_dict[name] = shopping_dict[name] + count
                else:
                    shopping_dict[name] = count
        for keys, values in shopping_dict.items():
            file.writelines(f'{keys} - {values}\n')
        file.close()
        with open(path, 'rb') as f:
            data = f.read()
        response = HttpResponse(data, content_type='text')
        response['Content-Disposition'] = f'filename={os.path.basename(path)}'
        file.close()
        return response


class FavoriteViewSet(CreateDestroyViewSet):
    """Обработка запросов `api/recipes/{id}/favorites`."""
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.select_related('user').all()
    permission_classes = [IsAuthenticated]

    @action(methods=['DELETE'], detail=True)
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('id'))
        if not Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(CreateDestroyViewSet):
    """Обработка запросов `api/user/{id}/subscribe`."""
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.select_related('user').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        limit = self.request.GET.get('recipes_limit', None)
        context = super().get_serializer_context()
        context.update({'recipes_limit': limit})
        return context

    @action(methods=['DELETE'], detail=True)
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        subscriber = get_object_or_404(User, id=self.kwargs.get('id'))
        if not Subscription.objects.filter(
            user=user,
            subscriber=subscriber
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.get(user=user, subscriber=subscriber).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingViewSet(CreateDestroyViewSet):
    """Обработка запросов `api/recipes/{id}/shopping_cart`."""
    serializer_class = ShoppingSerializer
    queryset = Shopping.objects.select_related('user').all()
    permission_classes = [IsAuthenticated]

    @action(methods=['DELETE'], detail=True, )
    def delete(self, request, *args, **kwargs):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('id'))
        if not Shopping.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        Shopping.objects.get(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
