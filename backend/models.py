# no longer needed use common/model.py

import logging
import os
from pathlib import Path
import numpy as np
from typing import List, Optional

from contextlib import asynccontextmanager
from datetime import datetime, date

from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from redis import asyncio

import joblib
from joblib import load
from pydantic import BaseModel, ConfigDict, Field, field_validator


# TODO: add validation checks

class Location(BaseModel):
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    postalCode: str
    country: str
    latitude: float
    longitude: float

class Place(BaseModel):
    name: str
    category: str
    location: Location
    description: str

class Activity(BaseModel):
    place: Place
    datetime: datetime
    description: str

class Itinerary(BaseModel):
    activities: List[Activity]

class UserPreference(BaseModel):
    destinationCity: str
    departureLocation: str
    fromDate: date
    toDate: date
    interested_categories: List[str]
    optimizedOptions: str  # e.g., ["by-weather", "by-traffic"]
