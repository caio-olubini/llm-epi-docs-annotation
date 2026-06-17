from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Disease(str, Enum):
    dengue = "dengue"
    chikungunya = "chikungunya"
    zika = "zika"
    febre_amarela = "febre_amarela"
    outro = "outro"


class LocationLevel(str, Enum):
    national = "national"
    region = "region"
    state = "state"
    municipality = "municipality"


class EpiObservation(BaseModel):
    disease: Disease = Field(description="Doença referida nesta observação.")
    location_name: str = Field(description="Local: 'Brasil', uma região, um estado (UF) ou 'Município/UF'.")
    location_level: LocationLevel = Field(description="Granularidade geográfica do local.")
    epi_week_start: int | None = Field(None, description="Primeira semana epidemiológica (SE) do período, 1–53.")
    epi_week_end: int | None = Field(None, description="Última semana epidemiológica (SE) do período, 1–53.")
    reference_year: int | None = Field(None, description="Ano de referência dos dados.")
    probable_cases: int | None = Field(None, description="Número de casos prováveis.")
    confirmed_cases: int | None = Field(None, description="Número de casos confirmados.")
    deaths: int | None = Field(None, description="Número de óbitos.")
    incidence_per_100k: float | None = Field(None, description="Taxa de incidência por 100 mil habitantes.")
    data_source: str | None = Field(None, description="Fonte dos dados, ex.: 'Sinan On-line', 'Sinan Net'.")


class DocumentAnnotation(BaseModel):
    diseases_covered: list[Disease] = Field(description="Doenças tratadas no boletim.")
    reference_year: int | None = Field(None, description="Ano principal de referência do boletim.")
    publication_date: date | None = Field(None, description="Data de publicação do boletim.")
    bulletin_volume: str | None = Field(None, description="Volume do boletim, ex.: '53'.")
    bulletin_number: str | None = Field(None, description="Número/edição do boletim, ex.: '21'.")
    observations: list[EpiObservation] = Field(
        default_factory=list,
        description="Todas as observações epidemiológicas extraídas.",
    )
