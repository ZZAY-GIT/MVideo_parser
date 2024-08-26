import json
import math
import os
from xlsxwriter.workbook import Workbook
import datetime

import requests
from modules.config import Links, headers, cookies


def get_data_MVideo(ids):
    params = {
        'categoryId': f'{ids}',
        'offset': '0',
        'limit': '24',
        'filterParams': 'WyLQotC+0LvRjNC60L4g0LIg0L3QsNC70LjRh9C40LgiLCItOSIsItCU0LAiXQ==',
    }

    if not os.path.exists('data'):
        os.mkdir('data')

    s = requests.Session()
    response = s.get('https://www.mvideo.ru/bff/products/listing', params=params, cookies=cookies,
                     headers=headers).json()

    total_items = response['body']['total']

    if total_items is None:
        return '[!] No items :('

    pages_count = math.ceil(total_items / 24)

    print(f'[INFO] Total positions: {total_items} | Total pages: {pages_count}')

    products_ids = {}
    products_description = {}
    products_prices = {}

    for i in range(pages_count):
        try:
            offset = f'{i * 24}'

            params = {
                'categoryId': f'{ids}',
                'offset': offset,
                'limit': '24',
                'filterParams': 'WyLQotC+0LvRjNC60L4g0LIg0L3QsNC70LjRh9C40LgiLCItOSIsItCU0LAiXQ==',
            }

            response = s.get('https://www.mvideo.ru/bff/products/listing', params=params, cookies=cookies,
                             headers=headers).json()

            products_ids_list = response['body']['products']
            products_ids[i] = products_ids_list

            json_data = {
                'productIds': products_ids_list,
                'mediaTypes': [
                    'images',
                ],
                'category': True,
                'status': True,
                'brand': True,
                'propertyTypes': [
                    'KEY',
                ],
                'propertiesConfig': {
                    'propertiesPortionSize': 5,
                },
                'multioffer': False,
            }
            response = s.post('https://www.mvideo.ru/bff/product-details/list', cookies=cookies, headers=headers,
                              json=json_data)
            print(f'[INFO] Response code: {response.status_code}')
            if response.status_code == 200:
                products_description[i] = response.json()
                products_ids_str = ','.join(products_ids_list)

                params = {
                    'productIds': products_ids_str,
                    'addBonusRubles': 'true',
                    'isPromoApplied': 'true',
                }

                response = s.get('https://www.mvideo.ru/bff/products/prices', params=params, cookies=cookies,
                                 headers=headers).json()
                material_prices = response['body']['materialPrices']

                for item in material_prices:
                    item_id = item['price']['productId']
                    item_base_price = item['price']['basePrice']
                    item_sale_price = item['price']['salePrice']
                    item_bonus = item['bonusRubles']['total']

                    products_prices[item_id] = {
                        'item_basePrice': item_base_price,
                        'item_salePrice': item_sale_price,
                        'item_bonus': item_bonus
                    }

                print(f'[+] Finished {i + 1} of the {pages_count} pages')
            else:
                print(f'[!] Skipped {i + 1} page')
        except Exception as e:
            print(f'[!] Skipped {i + 1} page', e.__class__.__name__)

    with open('data/1_product_ids.json', 'w', encoding='UTF-8') as file:
        json.dump(products_ids, file, indent=4, ensure_ascii=False)

    with open('data/2_product_description.json', 'w', encoding='UTF-8') as file:
        json.dump(products_description, file, indent=4, ensure_ascii=False)

    with open('data/3_product_prices.json', 'w', encoding='UTF-8') as file:
        json.dump(products_prices, file, indent=4, ensure_ascii=False)


def get_result(worksheet, center):
    row = 1
    n = 0
    with open('data/2_product_description.json', 'r', encoding='UTF-8') as file:
        products_data = json.load(file)

    with open('data/3_product_prices.json', 'r', encoding='UTF-8') as file:
        products_prices = json.load(file)

    for items in products_data.values():
        products = items['body']['products']

        for item in products:
            product_id = item.get('productId')

            if product_id in products_prices:
                prices = products_prices[product_id]
            item_name = items['body']['products'][n]['name']
            item_basePrice = prices['item_basePrice']
            item_salePrice = prices['item_salePrice']
            item_bonus = prices['item_bonus']
            item_link = f'https://www.mvideo.ru/products/{item["nameTranslit"]}-{product_id}'
            worksheet.write(row, 0, item_name, center)
            worksheet.write(row, 1, item_basePrice, center)
            worksheet.write(row, 2, item_salePrice, center)
            worksheet.write(row, 3, item_bonus, center)
            worksheet.write(row, 4, item_link)

            if n == len(items['body']['products']) - 1:
                n = 0
            else:
                n += 1
            row += 1


def get_categoryId(name):
    ids = {
        "Телевизоры": "65",
        "Ноутбуки": "118",
        "Смартфоны": "205",
        "Холодильники": "159",
        "Планшеты": "195",
        "Микроволновые печи": "94",
        'Кондиционеры': '106',
        'Стиральные машины': '89',
        'Смарт-часы': '400',
        "Пылесосы": "2428",
        'Наушники': '3967',
        "Компьютерные мыши": "183",
        "Клавиатуры": "217",
        "Тренажёры": "8411",
        "Электрочайники": "96",
        "Мультиварки": "180",
        "Мониторы": "101",
        "Посудомоечные машины": "160"
    }
    item_id = ids[name]
    return item_id


def parse(category):
    print("started")
    path = f'output\\{category}-{datetime.datetime.now().strftime("%d-%m-%Y")}.xlsx'
    if os.path.exists(path):
        return path
    workbook = Workbook(path)
    format = workbook.add_format({'bold': True, 'align': 'center'})
    center = workbook.add_format({'align': 'center'})
    worksheet = workbook.add_worksheet()
    worksheet.write(0, 0, 'Название', format)
    worksheet.write(0, 1, 'Цена', format)
    worksheet.write(0, 2, 'Цена со скидкой', format)
    worksheet.write(0, 3, 'Бонусы', format)
    worksheet.write(0, 4, 'Ссылка на товар', format)
    try:
        os.remove("data\\1_product_ids.json")
        os.remove("data\\2_product_description.json")
        os.remove("data\\3_product_prices.json")
    except Exception:
        pass
    get_data_MVideo(get_categoryId(category))
    get_result(worksheet, center)
    worksheet.autofit()
    workbook.close()
    return path
