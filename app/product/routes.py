# wine/app/product/routes.py:
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from app.database import aroma_list_collection, collection
from app.dependencies import CommonsDepList, CommonsDepStr
from app.models import Wine
from app.product.utils import process_wine, get_query_for_aroma_search

router_products = APIRouter()


@router_products.get("/catalog/", tags=["products"], response_model=list[Wine])
async def get_catalog(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []

    cursor = collection.find().limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/with-package/", tags=["products"], response_model=list[Wine])
async def get_catalog_with_package(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    cursor = (
        collection.find({"package": "подарункова упаковка"}).limit(limit).skip(skip)
    )
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


# countries must be a list of strings in format "Італія (Italy), Іспанія (Spain)"
@router_products.get("/by-country/", tags=["products"], response_model=list[Wine])
async def get_catalog_by_country(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    if query:
        country_names = [country.strip() for country in query.split(",")]
        query_conditions = [{"country": country_name} for country_name in country_names]
        query = {"$or": query_conditions}
    else:
        query = {}

    cursor = collection.find(query).limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/by-color/", tags=["products"], response_model=list[Wine])
async def get_catalog_by_color(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    if query:
        # query = {"color": {"$in": query}}
        color_names = [country.strip() for country in query.split(",")]
        query_conditions = [{"color": color_name} for color_name in color_names]
        query = {"$or": query_conditions}
    else:
        query = {}

    cursor = collection.find(query).limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/by-wine-type/", tags=["products"], response_model=list[Wine])
async def get_catalog_by_wine_type(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    if query:
        wine_types = [wine_type.strip() for wine_type in query.split(",")]
        query_conditions = [{"wine_type": wine_type} for wine_type in wine_types]
        query = {"$or": query_conditions}
    else:
        query = {}

    cursor = collection.find(query).limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


# query can be: "0.187, 0.2, 0.375, 0.75, 1.5, 6"
@router_products.get("/by-capacity/", tags=["products"], response_model=list[Wine])
async def get_catalog_by_capacity(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    if query:
        capacities = [capacity.strip() for capacity in query.split(",")]
        query_conditions = [{"capacity": capacity} for capacity in capacities]
        query = {"$or": query_conditions}
    else:
        query = {}

    cursor = collection.find(query).limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/catalog/{wine_id}/", tags=["products"], response_model=Wine)
async def get_bottle(wine_id: str):
    try:
        wine_id_obj = ObjectId(wine_id)
        wine = await collection.find_one({"_id": wine_id_obj})
        if wine:
            processed_wine = process_wine(wine)
            return processed_wine
        else:
            raise HTTPException(status_code=404, detail="Wine not found")
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid wine ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_products.get("/wine/", tags=["products"], response_model=list[Wine])
async def get_wine(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    wines = []
    cursor = collection.find({"kind": "wine"}).limit(limit).skip(skip)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/champagne/", tags=["products"], response_model=list[Wine])
async def get_champagne(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    champagne = []
    cursor = (
        collection.find({"kind": {"$in": ["prosecco", "Ігристе"]}})
        .limit(limit)
        .skip(skip)
    )
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        champagne.append(processed_wine)
    return champagne


@router_products.get("/aroma/", tags=["products"], response_model=list[Wine])
async def get_by_aroma(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]

    wines = []
    search_query = await get_query_for_aroma_search(query)

    cursor = collection.find(
        {'$text': {'$search': search_query}},
        {'score': {'$meta': 'textScore'}}
    ).sort([('score', {'$meta': 'textScore'})]).limit(limit).skip(skip)

    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        wines.append(processed_wine)
    return wines


@router_products.get("/aroma_mappings/", tags=["products"])
async def get_aroma_mappings():
    word_mappings = await aroma_list_collection.find_one()
    if not word_mappings:
        raise HTTPException(
            status_code=500, detail="Aroma word mappings not found in the database"
        )

    return list(word_mappings.keys())


@router_products.get("/food/", tags=["products"], response_model=list[Wine])
async def get_by_food(commons: CommonsDepStr):
    query = commons["query"]
    limit = commons["limit"]
    skip = commons["skip"]

    foods = []
    query_words = [word.strip() for word in query.split(",")]
    filter_query = {"gastronomic_combination": {"$in": query_words}}
    cursor = collection.find(filter_query).limit(limit).skip(skip)
    async for document in cursor:
        food = document.copy()
        processed_wine = process_wine(food)
        foods.append(processed_wine)
    return foods


@router_products.get("/romantic/", tags=["products"], response_model=list[Wine])
async def get_romantic(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    romantic_wines = []
    pipeline = [
        {"$match": {"wine_type": {"$in": ["Сододке", "Напівсолодке"]}}},
        {"$skip": skip},
        {"$sample": {"size": limit}},
    ]
    cursor = collection.aggregate(pipeline)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        romantic_wines.append(processed_wine)
    return romantic_wines


@router_products.get("/festive/", tags=["products"], response_model=list[Wine])
async def get_festive(commons: CommonsDepList):
    limit = commons["limit"]
    skip = commons["skip"]
    festive_wines = []
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"$and": [{"kind": "prosecco"}, {"wine_type": "Солодке"}]},
                    {"$and": [{"kind": "Ігристе"}, {"wine_type": "Солодке"}]},
                ]
            }
        },
        {"$skip": skip},
        {"$sample": {"size": limit}},
    ]
    cursor = collection.aggregate(pipeline)
    async for document in cursor:
        wine = document.copy()
        processed_wine = process_wine(wine)
        festive_wines.append(processed_wine)
    return festive_wines
