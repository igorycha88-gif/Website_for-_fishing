import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class YandexGeocoderService:
    BASE_URL = "https://geocode-maps.yandex.ru/1.x"

    async def geocode_address(
        self,
        address: str,
        limit: int = 1
    ) -> Optional[Dict[str, Any]]:
        params = {
            "apikey": settings.YANDEX_MAPS_API_KEY,
            "format": "json",
            "geocode": address,
            "lang": "ru_RU",
            "results": limit,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("response"):
                    features = data["response"]["GeoObjectCollection"]["featureMember"]
                    if features:
                        geo_object = features[0]["GeoObject"]
                        point = geo_object["Point"]["pos"]
                        lon, lat = point.split(" ")
                        return {
                            "latitude": float(lat),
                            "longitude": float(lon),
                            "address": geo_object["metaDataProperty"]["GeocoderMetaData"]["text"],
                            "precision": geo_object["metaDataProperty"]["GeocoderMetaData"]["precision"]
                        }
        except Exception as e:
            pass

        return None

    async def reverse_geocode(
        self,
        lat: float,
        lng: float
    ) -> Optional[str]:
        params = {
            "apikey": settings.YANDEX_MAPS_API_KEY,
            "format": "json",
            "geocode": f"{lng},{lat}",
            "lang": "ru_RU",
            "results": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("response"):
                    features = data["response"]["GeoObjectCollection"]["featureMember"]
                    if features:
                        geo_object = features[0]["GeoObject"]
                        return geo_object["metaDataProperty"]["GeocoderMetaData"]["text"]
        except Exception as e:
            pass

        return None

    async def reverse_geocode_detailed(
        self,
        lat: float,
        lng: float
    ) -> Optional[Dict[str, str]]:
        params = {
            "apikey": settings.YANDEX_MAPS_API_KEY,
            "format": "json",
            "geocode": f"{lng},{lat}",
            "lang": "ru_RU",
            "results": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("response"):
                    features = data["response"]["GeoObjectCollection"]["featureMember"]
                    if features:
                        geo_object = features[0]["GeoObject"]
                        address = geo_object["metaDataProperty"]["GeocoderMetaData"]["text"]
                        meta_data = geo_object["metaDataProperty"]["GeocoderMetaData"]
                        
                        address_parts = meta_data.get("Address", {})
                        components = address_parts.get("Components", [])
                        
                        city = None
                        region = None
                        country = None
                        
                        for component in components:
                            kind = component.get("kind")
                            name = component.get("name")
                            
                            if kind == "locality":
                                city = name
                            elif kind == "province":
                                region = name
                            elif kind == "country":
                                country = name
                        
                        return {
                            "address": address,
                            "city": city,
                            "region": region,
                            "country": country
                        }
        except Exception as e:
            pass

        return None


yandex_geocoder = YandexGeocoderService()
