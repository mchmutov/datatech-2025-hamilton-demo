from enum import Enum
from typing import Dict, Tuple
from datetime import date
from pydantic import BaseModel


class KMA(str, Enum):
    CA_STK = "CA_STK"
    CA_LAX = "CA_LAX"
    AZ_PHO = "AZ_PHO"
    TX_DAL = "TX_DAL"
    TX_HOU = "TX_HOU"
    NJ_ELI = "NJ_ELI"
    IL_CHI = "IL_CHI"
    IN_IND = "IN_IND"
    MN_MIN = "MN_MIN"
    WI_MIL = "WI_MIL"
    FL_LAK = "FL_LAK"
    GA_ATL = "GA_ATL"


# Default coordinates (latitude, longitude) for each KMA
KMA_DEFAULT_COORDINATES: Dict[KMA, Tuple[float, float]] = {
    KMA.CA_STK: (37.9577, -121.2908),  # Stockton, California
    KMA.CA_LAX: (34.0522, -118.2437),  # Los Angeles, California
    KMA.AZ_PHO: (33.4484, -112.0740),  # Phoenix, Arizona
    KMA.TX_DAL: (32.7767, -96.7970),  # Dallas, Texas
    KMA.TX_HOU: (29.7604, -95.3698),  # Houston, Texas
    KMA.NJ_ELI: (40.6639, -74.2107),  # Elizabeth, New Jersey
    KMA.IL_CHI: (41.8781, -87.6298),  # Chicago, Illinois
    KMA.IN_IND: (39.7684, -86.1581),  # Indianapolis, Indiana
    KMA.MN_MIN: (44.9778, -93.2650),  # Minneapolis, Minnesota
    KMA.WI_MIL: (43.0389, -87.9065),  # Milwaukee, Wisconsin
    KMA.FL_LAK: (28.0395, -81.9498),  # Lakeland, Florida
    KMA.GA_ATL: (33.7490, -84.3880),  # Atlanta, Georgia
}


class Location(BaseModel):
    kma: KMA
    latitude: float
    longitude: float

    @classmethod
    def from_kma(cls, kma: KMA) -> "Location":
        """
        Create a Location instance using default coordinates for a given KMA.
        """
        if kma not in KMA_DEFAULT_COORDINATES:
            raise ValueError(f"No default coordinates defined for KMA: {kma}")

        lat, lon = KMA_DEFAULT_COORDINATES[kma]
        return cls(kma=kma, latitude=lat, longitude=lon)


class Load(BaseModel):
    id: str
    origin: Location
    destination: Location
    miles: int
    pickup_date: date
    cost: float
    weight: int
