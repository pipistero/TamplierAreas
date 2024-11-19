import requests
from shapely.geometry import shape, Point


# Загрузка GeoJSON файла
def load_geojson(geojson_path):
    import json
    with open(geojson_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Проверка, находится ли точка в зоне
def is_point_in_zone(latitude, longitude, geojson_data):
    point = Point(longitude, latitude)
    for feature in geojson_data['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return feature['properties'].get('description', 'Zone')
    return None


# Функция для получения всех элементов смарт-процесса с учетом пагинации
def get_all_smart_process_items():
    all_items = []
    start = 0
    limit = 50  # Количество элементов на странице

    while True:
        url = 'https://bitrix.aliton.ru/rest/2460/0wgpqk9iyrtl5t8r/crm.company.list.json'
        params = {
            'select': [
                'UF_CRM_1725013332',
                'ID'
            ],
            'start': start
        }
        response = requests.post(url, json=params)

        if response.status_code == 200:
            data = response.json()
            items = data.get('result', {}).get('items', [])
            all_items.extend(items)

            if len(items) < limit:
                break

            start += limit
        else:
            print(f"Error fetching items: {response.status_code}")
            break

    return all_items


# Функция для обновления данных смарт-процесса
def update_smart_process_item(item_id, zone_name):
    url = 'https://bitrix.aliton.ru/rest/2460/0wgpqk9iyrtl5t8r/crm.company.update.json'
    data = {
        'id': item_id,
        'fields': {
            'UF_CRM_1725013395': zone_name
        }
    }
    response = requests.post(url, json=data)
    return response.status_code == 200


# Основной код для обработки всех элементов смарт-процесса
def process_all_smart_items(geojson_data):
    items = get_all_smart_process_items()

    if not items:
        print("No smart process items found.")
        return

    for item in items:
        try:
            item_id = item.get('id')
            coordinates = item.get('ufCrm44_1724363546')

            if coordinates:
                try:
                    latitude, longitude = map(float, map(str.strip, coordinates.split(',')))
                    zone_name = is_point_in_zone(latitude, longitude, geojson_data)

                    if zone_name:
                        update_smart_process_item(item_id, zone_name)
                        print(f"Smart process item {item_id} updated with zone: {zone_name}")
                    else:
                        # Если координаты не попадают ни в одну зону
                        update_smart_process_item(item_id, "Координаты не попадают в зону области")
                        print(
                            f"Smart process item {item_id} updated with zone: 'Координаты не попадают в зону области'")
                except Exception as e:
                    print(f"Error processing coordinates for item {item_id}: {e}")
            else:
                print(f"Coordinates not found for item {item_id}")

        except Exception as e:
            print(f"Error processing item {item_id}: {e}")


# Загрузка GeoJSON и запуск обработки
geojson_data = load_geojson('Эльтон_15-10-2024_14-23-35.geojson')
process_all_smart_items(geojson_data)
