from enum import Enum
from pydantic import BaseModel, Field


class Disease(str, Enum):
    dengue = "dengue"; chikungunya = "chikungunya"; zika = "zika"

class Trend(str, Enum):  # direção narrativa afirmada pelo texto
    decrease = "queda"; normal = "normal"; increase = "alta"; not_reported = "nao_informado"

class Concern(str, Enum):  # nível de preocupação/alarme afirmado pelo texto
    low = "baixa"; normal = "normal"; high = "alta"; very_high = "muito_alta"; not_reported = "nao_informado"

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


class NationalSignal(BaseModel):
    """Sinal narrativo no nível nacional (território = Brasil) para uma doença."""
    disease: Disease = Field(description="Doença a que o sinal se refere.")
    trend: Trend = Field(description="Direção narrativa afirmada para os casos no Brasil.")
    concern: Concern = Field(description="Nível de preocupação afirmado no nível nacional.")


class TerritorySignal(BaseModel):
    """Sinal narrativo para um par (doença × território) destacado no boletim."""
    territory: str = Field(description="Região, estado (UF) ou município destacado.")
    disease: Disease = Field(description="Doença a que o sinal se refere.")
    trend: Trend = Field(description="Direção narrativa afirmada para os casos no território.")
    concern: Concern = Field(description="Nível de preocupação afirmado para o território.")


class SerotypeSignal(BaseModel):
    """Afirmação sobre circulação de sorotipo de dengue em um território."""
    territory: str = Field(description="'Brasil', região, estado (UF) ou município.")
    serotype: Serotype = Field(description="Sorotipo de dengue em foco.")
    trend: Trend = Field(description="Direção narrativa afirmada para o sorotipo (ex.: em alta se predominante/em expansão).")


class ActionSignal(BaseModel):
    """Ações de resposta realizadas em um território."""
    territory: str = Field(description="'Brasil', região, estado (UF) ou município.")
    actions: list[Intervention] = Field(description="Ações de resposta afirmadas para o território.")


class DocumentAnnotation(BaseModel):
    # Nível relatório
    reference_year: int | None = Field(None, description="Ano de referência dos dados do boletim.")
    publication_date: str | None = Field(None, description="Data de publicação no formato MM/YYYY (mês/ano).")
    diseases_in_focus: list[Disease] = Field(description="Doenças em foco no boletim.")

    # Nível nacional (território = Brasil)
    national: list[NationalSignal] = Field(
        default_factory=list, description="Sinais no nível nacional (Brasil), um por doença destacada.")

    # Por território (regiões, estados, cidades)
    by_territory: list[TerritorySignal] = Field(
        default_factory=list, description="Sinais para territórios destacados; mantenha enxuto.")

    # Sorotipos
    serotypes: list[SerotypeSignal] = Field(
        default_factory=list, description="Afirmações sobre sorotipos de dengue por território.")

    # Ações realizadas
    actions: list[ActionSignal] = Field(
        default_factory=list, description="Ações de resposta realizadas, por território.")
