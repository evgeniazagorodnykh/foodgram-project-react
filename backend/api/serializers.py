import base64

import webcolors
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer, UserCreateSerializer
from django.shortcuts import get_object_or_404


from recipe.models import (
    Recipe,
    Ingredient,
    IngredientRecipe,
    Tag,
    TagRecipe,
    Subscription,
    Favorite,
    Shopping
)


User = get_user_model()


class Hex2NameColor(serializers.Field):
    """Сериализатор поля цвета тега."""
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    """Сериализатор поля картинки рецепта."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор модели `User` для регистрации."""
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+\Z',
        max_length=150,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    email = serializers.EmailField(max_length=254, required=True)
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        max_length=150,
        required=True,
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели `User` для вывода."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        if self.context.get('request').user.is_authenticated:
            user = self.context.get('request').user
            return Subscription.objects.filter(
                user=user, subscriber=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Tag`."""
    slug = serializers.SlugField(
        max_length=200,
        validators=[UniqueValidator(queryset=Tag.objects.all())]
    )
    color = Hex2NameColor()
    name = serializers.CharField(max_length=200)

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Tag.objects.all(),
                fields=['name', 'color', 'slug']
            )
        ]


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Ingredient`."""
    name = serializers.CharField(max_length=200, required=True)
    measurement_unit = serializers.CharField(max_length=200, required=True)

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class IngredientCreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Ingredient` для создания рецепта."""
    amount = serializers.IntegerField(min_value=1)
    id = serializers.IntegerField(min_value=1, source='ingredient__id')

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'amount',
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Ingredient` для вывода рецепта."""
    amount = serializers.IntegerField(min_value=1)
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class TagRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Tag` для вывода рецепта."""
    name = serializers.CharField(source='tag.name')
    color = serializers.CharField(source='tag.color')
    slug = serializers.CharField(source='tag.slug')

    class Meta:
        model = TagRecipe
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Recipe` для создания рецепта."""
    image = Base64ImageField(required=True)
    ingredients = IngredientCreateRecipeSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    cooking_time = serializers.IntegerField(min_value=1, required=True)
    author = CustomUserSerializer(
        read_only=True,
    )
    name = serializers.CharField(max_length=200, required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нельзя добавить рецепт без ингредиентов')
        ingredient_set = {ingredient['ingredient__id'] for ingredient in value}
        if len(value) != len(ingredient_set):
            raise serializers.ValidationError(
                'Нельзя дважды добавить ингредиент')
        for ingredient in ingredient_set:
            if not Ingredient.objects.filter(id=ingredient).exists():
                raise serializers.ValidationError(
                    'Нельзя добавить несуществующий ингредиент')
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нельзя добавить рецепт без тегов')
        tags_set = set(value)
        if len(value) != len(tags_set):
            raise serializers.ValidationError(
                'Нельзя дважды добавить тег')
        for tag in tags_set:
            if not Tag.objects.filter(id=tag.id).exists():
                raise serializers.ValidationError(
                    'Нельзя добавить несуществующий тег')
        return value

    def create_ingredients(self, ingredients, recipe):
        ingredient_list = []
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                id=ingredient.pop('ingredient__id')
            )
            ingredient_list.append(
                IngredientRecipe.objects.create(
                    ingredient=current_ingredient,
                    amount=ingredient.pop('amount'),
                    recipe=recipe
                )
            )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients_data, instance)
        else:
            raise serializers.ValidationError(
                'Нельзя изменить рецепт без ингредиентов')
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.clear()
            instance.tags.set(tags_data)
        else:
            raise serializers.ValidationError(
                'Нельзя изменить рецепт без тегов')
        instance.save()
        return instance

    def to_representation(self, obj):
        return RecipeReadSerializer(
            obj,
            context={
                'request': self.context.get('request')
            },
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Recipe` для вывода рецепта."""
    image = Base64ImageField(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(
        Tag.objects.all(),
        many=True,
    )
    cooking_time = serializers.IntegerField(read_only=True, min_value=1)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        if self.context.get('request').user.is_authenticated:
            user = self.context.get('request').user
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context.get('request').user.is_authenticated:
            user = self.context.get('request').user
            return Shopping.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_ingredients(self, obj):
        ingredients = IngredientRecipe.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Favorite`."""
    name = serializers.CharField(read_only=True, source='recipe.name')
    image = serializers.CharField(read_only=True, source='recipe.image')
    cooking_time = serializers.IntegerField(
        read_only=True,
        source='recipe.cooking_time'
    )

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

    def create(self, validated_data):
        user = self.context.get('request').user
        my_view = self.context['view']
        id = my_view.kwargs.get('id')
        if not Recipe.objects.filter(id=id).exists():
            raise serializers.ValidationError(
                'Нельзя добавить несуществующий рецепт')
        recipe = Recipe.objects.get(id=id)
        if Favorite.objects.filter(
                user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Нельзя дважды добавить рецепт в избранное')
        return Favorite.objects.create(user=user, recipe=recipe)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Recipe` для вывода в подписках."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Subscription`."""
    username = serializers.SlugField(read_only=True, source='subscriber.username')
    email = serializers.EmailField(read_only=True, source='subscriber.email')
    first_name = serializers.CharField(read_only=True, source='subscriber.first_name')
    last_name = serializers.CharField(read_only=True, source='subscriber.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.subscriber).all()
        limit = self.context.get('recipes_limit')
        print(limit)
        if limit:
            recipes = recipes[:int(limit)]
        print(recipes)
        return RecipeShortSerializer(
            recipes,
            many=True
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.subscriber).count()

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(user=obj.user, subscriber=obj.subscriber).exists()

    def create(self, validated_data):
        user = self.context.get('request').user
        my_view = self.context['view']
        id = my_view.kwargs.get('id')
        subscriber = get_object_or_404(User, id=id)
        if subscriber == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя')
        if Subscription.objects.filter(
                user=user, subscriber=subscriber).exists():
            raise serializers.ValidationError(
                'Нельзя дважды подписаться на одного пользователя')
        return Subscription.objects.create(user=user, subscriber=subscriber)


class ShoppingSerializer(serializers.ModelSerializer):
    """Сериализатор модели `Shopping`."""
    name = serializers.CharField(read_only=True, source='recipe.name')
    image = serializers.CharField(read_only=True, source='recipe.image')
    cooking_time = serializers.IntegerField(read_only=True, source='recipe.cooking_time')

    class Meta:
        model = Shopping
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

    def create(self, validated_data):
        user = self.context.get('request').user
        my_view = self.context['view']
        id = my_view.kwargs.get('id')
        if not Recipe.objects.filter(id=id).exists():
            raise serializers.ValidationError(
                'Нельзя добавить несуществующий рецепт')
        recipe = Recipe.objects.get(id=id)
        if Shopping.objects.filter(
                user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже есть в списоке покупок')
        return Shopping.objects.create(user=user, recipe=recipe)
