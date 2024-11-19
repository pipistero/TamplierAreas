import json
import requests
import re
from shapely.geometry import shape, Point


FILE_PATH = "Эльтон_18-11-2024_23-05-26.geojson"


def load_geojson_file():
    global FILE_PATH

    with open(FILE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_coordinates(coordinates_string):
    if (coordinates_string == None):
        return False

    coordinate_pattern = r"^\s*(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)\s*$"

    match = re.match(coordinate_pattern, coordinates_string)
    if not match:
        return False

    latitude, longitude = map(float, match.groups())
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def get_matching_area(geo_data, coordinates_string):
    if (validate_coordinates(coordinates_string) == False):
        return None

    coordinates = coordinates_string.split(", ")
    point = Point(coordinates[1], coordinates[0])

    matching_area = None
    for feature in geo_data.get("features", []):
        geometry = shape(feature["geometry"])
        if geometry.contains(point):
            matching_area = feature
            break

    return matching_area


def get_area_name(area):
    if (area):
        return area.get("properties", {})["description"]
    else:
        return None


def get_companies(start):
    url = 'https://bitrix.aliton.ru/rest/2460/0wgpqk9iyrtl5t8r/crm.company.list.json'
    payload = {
        'select': [
            'UF_CRM_1725013332',
            'id'
        ],
        'start': start
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()['result']

    except requests.exceptions.RequestException as e:
        print(f"Error fetching companies! Error - {e}")
        return None


def get_all_companies(start, limit):
    all_companies = []
    step = 50

    if (start < 0):
        start = 0

    last_id = 0
    last_company_id = 0

    while True:
        companies = get_companies(start)

        if (companies):
            companies_len = len(companies)
            last_company_id = int(companies[companies_len - 1]['ID'])
            
            if (last_id > last_company_id):
                break
            last_id = last_company_id

            all_companies.extend(companies)
            print(f"Got {companies_len} companies; Total companies count - {len(all_companies)}")

            start += step
            if (start >= limit):
                break

        else:
            print("Got None companies!!")

    print(f"Total companies - {len(all_companies)}")
    return all_companies


def get_area_id(area_name):
    match area_name:
        case "Юг":
            return "14669"
        case "Юг2":
            return "14768"
        case "Центр":
            return "14668"
        case "Центр 2":
            return "14767"
        case "Север":
            return "14667"
        case "Север2":
            return "14766"
        case None:
            return "14834"
    return "14834"


def update_company_area(company_id, area_name):
    area_id = get_area_id(area_name)
    url = 'https://bitrix.aliton.ru/rest/2460/0wgpqk9iyrtl5t8r/crm.company.update.json'
    payload = {
        'id': company_id,
        'fields': {
            'UF_CRM_1725013395': area_id
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Set for company with id ({company_id}) area name ({area_name}, {area_id})")
        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        print(f"Error updating company! Company ID - {company_id}; Error - {e}")
        return False


def operate_all_companies(companies, geo_data):
    operated_companies = 0

    for company in companies:
        company_id = company['ID']
        company_coordinates = company['UF_CRM_1725013332']

        if (not company_coordinates):
            print(f"Operation for company ({company_id}) stopped; Cause - coordinates none")
            continue
        else:
            print(f"Operation for company ({company_id}) execution")

        area = get_matching_area(geo_data, company_coordinates)
        area_name = get_area_name(area)
        
        update_company_area(company_id, area_name)

        operated_companies += 1

        if (operated_companies % 100 == 0):
            print(f"Operated companies - {operated_companies}")

    print()
    print(f"Companies operations done!")
    print(f"Total companies - {len(companies)}")
    print(f"Total updated companies - {operated_companies}")


if __name__ == '__main__':
    geo_data = load_geojson_file()
    companies = get_all_companies(3000, 14000)

    operate_all_companies(companies, geo_data)