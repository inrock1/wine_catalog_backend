import os

import requests
import scrapy
from scrapy.http import Response

from ..items import WineItem

HEADER_MAPPING = {
    "Назва укр.": "name",
    "Колір": "color",
    "Тип": "wine_type",
    "Бренд": "brand",
    "Літраж": "capacity",
    "В ящику шт.": "in_box",
    "Упаковка": "package",
    "Міцність": "alcohol_percentage",
    "Країна": "country",
    "Регіон": "region",
    "Виробник": "producer",
    "Форма келиху": "glass",
    "Подавати за температури, С": "temperature",
    "Гастрономічне поєднання": "gastronomic_combination",
    "Виноград": "grape",
    "Вінтаж": "vintage",
    "Чи потрібна декантація": "decantation",
    "Діаметр пляшки": "diameter",
    "Постачальник": "supplier",
}


def download_image(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)


class SpiderWinesSpider(scrapy.Spider):
    name = "spider-wines"
    allowed_domains = ["vino.ua"]

    def start_requests(self):
        for i in range(1, 62):
            url = f"https://vino.ua/ua/vino/filter/page={i}/"
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: Response, **kwargs):
        hrefs = response.css(
            ".catalogCard-main .catalogCard-view a::attr(href)"
        ).getall()
        for href in hrefs:
            yield response.follow(href, self.parse_wine)

    @staticmethod
    def parse_wine(response: Response):
        filename = f"wines.html"
        with open(filename, "wb") as f:
            f.write(response.body)

        data = WineItem()
        data["kind"] = "wine"

        rows = response.css("table.product-features__table tr")

        for row in rows:
            header = row.css("th::text").get()
            cell = row.css("td")

            if len(cell) > 0:
                if cell.css("a"):
                    value = cell.css("a::text").get()
                else:
                    value = cell.css("td::text").get()

            if header and value:
                header = header.strip()
                value = value.strip()

                if header in HEADER_MAPPING:
                    field_name = HEADER_MAPPING[header]
                    data[field_name] = value

        price = response.css(".product-price__item::text").get()
        data["price"] = price

        image_url = response.css("span.gallery__link::attr(data-href)").get()
        data["image_url"] = "https://vino.ua" + image_url
        filename = os.path.basename(data["image_url"])
        image_path = os.path.join("images", filename)
        download_image(data["image_url"], image_path)

        small_image_url = response.css("img.gallery__photo-img::attr(src)").get()
        data["small_image_url"] = "https://vino.ua" + small_image_url
        filename = os.path.basename(data["small_image_url"])
        image_path = os.path.join("images", filename)
        download_image(data["small_image_url"], image_path)

        description_mapping = {
            "Смак:": "name",
            "Колір:": "color",
            "Аромат:": "aroma",
            "Гастрономія:": "gastronomic",
            "Чому варто це купити.": "why_buy",
        }
        description = {}

        description_titles = response.css(
            ".product-description.j-product-description .text strong::text"
        ).getall()
        description_paragraphs = response.css(
            ".product-description.j-product-description .text p::text"
        ).getall()
        for i in range(5):
            title = description_titles[i]
            paragraph = description_paragraphs[i]
            if title and paragraph:
                title = title.strip()
                paragraph = paragraph.strip()
                if title in description_mapping:
                    field_name = description_mapping[title]
                    description[field_name] = paragraph
        data["description"] = description
        yield data


#  run with command line: scrapy crawl spider-wines
