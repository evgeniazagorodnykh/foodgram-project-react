from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(max_length=200, verbose_name='Название')
    measurement_unit = models.CharField(max_length=200, verbose_name='Единицы измерения')

    class Meta:
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    color = models.CharField(
        max_length=16, 
        verbose_name='Цвет'
    )
    slug = models.SlugField(
        unique=True, 
        max_length=200,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    """Модель рецепта."""
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Теги'
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка'
    )

    class Meta:
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name} {self.author}'


class IngredientRecipe(models.Model):
    """Модель связи ингредиента и рецепта."""
    ingredient = models.ForeignKey(
        Ingredient, 
        on_delete=models.CASCADE, 
        related_name='ingredient_recipe'
    )
    amount = models.PositiveIntegerField(verbose_name='Количество')
    recipe = models.ForeignKey(
        Recipe, 
        on_delete=models.CASCADE, 
        related_name='ingredient_recipe'
    )

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    """Модель связи тега и рецепта."""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tag} {self.recipe}'
    

class Subscription(models.Model):
    """Модель подписки."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='is_subscribed')
    

class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='favorites')


class Shopping(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shoppings')
