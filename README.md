# Foodgram

<img width="946" alt="image" src="https://github.com/evgeniazagorodnykh/foodgram-project-react/assets/129388336/f4168729-cab6-418f-acd3-7dfbfe1716ef">

## Описание

Через Foodgram пользователи могут делиться своими рецептами и добавлять к ним их фотографии. А также следить за новыми рецептами других пользователей, добавлять понравившиеся во вкладку избранное и загружать список покупок.

## Как запустить проект на сервере:

Создайте на своем сервере в директорию foodgram/  и скопируйте файл docker-compose.production.yml. Сделать это можно, например, при помощи утилиты SCP:
```
scp -i path_to_SSH/SSH_name docker-compose.production.yml \
    username@server_ip:/home/username/foodgram/docker-compose.production.yml
```
Выполните эту команду на сервере в папке foodgram/:
```
sudo docker compose -f docker-compose.production.yml up -d
```
Выполните миграции, соберите статические файлы бэкенда и скопируйте их в /backend_static/static/:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/static_django/. /static_django/
```
Обновите конфиг Nginx и переагрузите его.
Откройте в браузере страницу проекта https://foodblog.serveblog.net/

# Автор проекта:
[Евгения Загородных](https://github.com/evgeniazagorodnykh)\

