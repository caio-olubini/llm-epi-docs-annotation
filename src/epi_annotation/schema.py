from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class Disease(str, Enum):
    dengue = "dengue"; chikungunya = "chikungunya"; zika = "zika"
    febre_amarela = "febre_amarela"; sarampo = "sarampo"; outro = "outro"

class LocationLevel(str, Enum):
    national = "national"; region = "region"; state = "state"; municipality = "municipality"

class Trend(str, Enum):  # direção narrativa afirmada pelo texto
    strong_decrease = "strong_decrease"; decrease = "decrease"; stable = "stable"
    increase = "increase"; strong_increase = "strong_increase"; unclear = "unclear"

class VsExpected(str, Enum):  # relativo ao esperado/sazonal/ano anterior
    below = "below"; in_line = "in_line"; above = "above"
    well_above = "well_above"; not_stated = "not_stated"

class AlertLevel(str, Enum):  # postura oficial / escalonamento
    normal = "normal"; attention = "attention"; alert = "alert"
    epidemic = "epidemic"; emergency = "emergency"; not_stated = "not_stated"

class Serotype(str, Enum):
    denv1 = "DENV-1"; denv2 = "DENV-2"; denv3 = "DENV-3"; denv4 = "DENV-4"

class Intervention(str, Enum):
    vaccination = "vaccination"          # ex.: Qdenga no SUS
    vector_control = "vector_control"    # fumacê/UBV, controle do vetor
    mobilization = "mobilization"        # mutirão, força-tarefa
    emergency_declaration = "emergency_declaration"
    surveillance_intensification = "surveillance_intensification"
    public_communication = "public_communication"


class SignalRow(BaseModel):
    """Sinal narrativo para um par (doença × local) DESTACADO no boletim."""
    disease: Disease
    location_name: str = Field(description="'Brasil', região, UF ou 'Município/UF'.")
    location_level: LocationLevel
    epi_week_ref: int | None = Field(None, description="SE de referência do sinal, 1–53.")

    trend: Trend = Field(description="Direção narrativa afirmada para casos.")
    vs_expected: VsExpected = Field(VsExpected.not_stated)
    alert_level: AlertLevel = Field(AlertLevel.not_stated)
    severe_signal: bool = Field(False, description="Texto enfatiza óbitos/casos graves/pressão hospitalar.")
    forward_warning: bool = Field(False, description="Alerta de aumento esperado / início do período sazonal.")

    serotypes_mentioned: list[Serotype] = Field(default_factory=list)
    new_or_predominant_serotype: Serotype | None = Field(
        None, description="Sorotipo recém-introduzido ou tornado predominante (indicador antecedente forte).")
    interventions: list[Intervention] = Field(default_factory=list)

    # âncoras numéricas OPCIONAIS, só para grounding — não exaustivas
    probable_cases: int | None = None
    incidence_per_100k: float | None = None


class DocumentAnnotation(BaseModel):
    diseases_covered: list[Disease]
    reference_year: int | None = None
    publication_date: date | None = None
    bulletin_volume: str | None = None
    bulletin_number: str | None = None
    epi_week_end: int | None = Field(None, description="Última SE coberta pelo boletim.")

    overall_concern: AlertLevel = Field(
        AlertLevel.not_stated, description="Tom/alarme geral do documento (um escalar de gestalt).")
    primary_focus_locations: list[str] = Field(
        default_factory=list, description="Poucos locais que o boletim de fato destaca.")
    signals: list[SignalRow] = Field(
        default_factory=list, description="Sinais narrativos apenas para pares (doença × local) salientes; mantenha enxuto (~≤8).")