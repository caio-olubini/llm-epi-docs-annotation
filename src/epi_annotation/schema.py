from enum import Enum
from pydantic import BaseModel, Field


class Disease(str, Enum):
    dengue = "dengue"; chikungunya = "chikungunya"; zika = "zika"
    febre_amarela = "febre_amarela"; sarampo = "sarampo"; outro = "outro"

class LocationLevel(str, Enum):
    national = "nacional"; region = "regiao"; state = "estado"; municipality = "municipio"

class Trend(str, Enum):  # direção narrativa afirmada pelo texto
    strong_decrease = "forte_queda"; decrease = "queda"; stable = "estavel"
    increase = "alta"; strong_increase = "forte_alta"; unclear = "indefinido"

class Severity(str, Enum):  # gravidade/escalonamento afirmado (clínico + postura oficial)
    normal = "normal"; attention = "atencao"; severe = "grave"
    epidemic = "epidemia"; emergency = "emergencia"; not_stated = "nao_informado"

class Serotype(str, Enum):
    denv1 = "DENV-1"; denv2 = "DENV-2"; denv3 = "DENV-3"; denv4 = "DENV-4"

class Intervention(str, Enum):
    vaccination = "vacinacao"                          # ex.: Qdenga no SUS
    vector_control = "controle_vetorial"               # fumacê/UBV, controle do vetor
    mobilization = "mobilizacao"                       # mutirão, força-tarefa
    emergency_declaration = "declaracao_emergencia"
    surveillance_intensification = "intensificacao_vigilancia"
    public_communication = "comunicacao_publica"
    other = "outra"                                      # qualquer outra ação de resposta


class SignalRow(BaseModel):
    """Sinal narrativo para um par (doença × local) DESTACADO no boletim."""
    disease: Disease = Field(description="Doença a que o sinal se refere.")
    location_name: str = Field(description="'Brasil', região, UF ou 'Município/UF'.")
    location_level: LocationLevel = Field(description="Granularidade geográfica do local.")
    epi_week_ref: int | None = Field(None, description="Semana epidemiológica de referência do sinal, 1–53.")

    trend: Trend = Field(description="Direção narrativa afirmada para os casos.")
    severity: Severity = Field(
        Severity.not_stated,
        description="Gravidade afirmada: 'grave' para óbitos/casos graves/pressão hospitalar; 'epidemia'/'emergencia' para escalonamento oficial.")

    serotypes_mentioned: list[Serotype] = Field(default_factory=list, description="Sorotipos de dengue citados no contexto do sinal.")
    new_or_predominant_serotype: Serotype | None = Field(
        None, description="Sorotipo recém-introduzido ou tornado predominante (indicador antecedente forte).")
    interventions: list[Intervention] = Field(default_factory=list, description="Ações de resposta associadas ao sinal.")


class DocumentAnnotation(BaseModel):
    diseases_covered: list[Disease] = Field(description="Doenças efetivamente abordadas pelo boletim.")
    reference_year: int | None = Field(None, description="Ano de referência dos dados do boletim.")
    publication_date: str | None = Field(None, description="Data de publicação, ISO YYYY-MM-DD.")
    bulletin_volume: str | None = Field(None, description="Volume do boletim, se declarado.")
    bulletin_number: str | None = Field(None, description="Número/edição do boletim, se declarado.")
    epi_week_end: int | None = Field(None, description="Última semana epidemiológica coberta pelo boletim, 1–53.")

    overall_concern: Severity = Field(
        Severity.not_stated, description="Tom de alarme geral do documento (gestalt).")
    primary_focus_locations: list[str] = Field(
        default_factory=list, description="Poucos locais que o boletim de fato destaca.")
    signals: list[SignalRow] = Field(
        default_factory=list, description="Sinais para pares (doença × local) salientes; mantenha enxuto (~≤8).")