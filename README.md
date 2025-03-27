# Генератор схем на основе полезной нагрузки из HAR файлов или json файлов на основе ответа от api

## Настройка venv и проекта
### 1. Создание виртуального окружения и установка зависимостей

Создание venv с python 3.13
```shell
python3.13 -m venv myenv
```
Активация созданного venv
```shell
source myenv/bin/activate
```

#### Установка зависимостей

Обновление PIP
```shell
pip install --upgrade pip
```
Установка всех библиотек из requirements.txt
```shell
pip install -r requirements.txt
```

### 2. Создать и настроить .env файл
```API_KEY={API_KEY}```

```URL={URL}```

## Конфигурация генератора
Конфигурация генератора в двух файлах ```src/configs/config.ini``` и ```src/configs/config.json```
С помощью ```src/configs/config.py``` пересоздается и читается ```config.ini```, и читается ```config.json```

## Данные для запуска приложения
В каталоге /dumps/ есть две директории:
1. ```api/*/``` В ней сабдиректории с названиями эндпоинтов, в которых response в формате .json
2. ```har/``` В ней .har файлы

## Результат работы приложения
В директории ```/schemes/``` будут созданы сабдиректории соответствующие одному эндпоинту. Внутри будут json scheme для request и response

## Как добавить новый эндпоинт для сбора респонсов
1. В config.json в массив ENDPOINTS добавить наименование эндпоинта
2. В config.py добавить url для этого эндпоинта, чтобы он попал в config.ini
3. В config.json добавить объект в виде PAYLOAD или QUERY_PARAM
4. В класс APIHandler добавить метод типа _collect_responses_for_endpoint_name(self, ...). В методе вызывается метод 
self._api_handler также, как и в других методах
5. Новый метод _collect_responses_for_endpoint_name(self, ...) добавить в метод collect_responses

## Как запускать приложение
В блоке ```if __name__ == '__main__':``` при вызове main в аргументах указать только один True для from_har или from_api.
- ```from_har=True``` Прочитаются и распарьсятся ```.har``` файлы в ```/dumps/har/```, затем для каждого fetch/xhr будет создана json scheme
- ```from_api=True``` Прочитаются ```.json``` файлы в ```/dumps/api/*/```, затем для каждой сабдиректории будет создана одна json scheme

```shell
python3.13 main.py
```
