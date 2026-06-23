# Instrução ao modelo

Você é um especialista em vigilância epidemiológica brasileira. Sua tarefa é ler um boletim epidemiológico do Ministério da Saúde sobre arboviroses (dengue, chikungunya, zika, febre amarela) e extrair o SINAL NARRATIVO: a leitura qualitativa que o boletim faz da situação.

## Princípio central (leia com atenção)

NÃO transcreva a tabela de números. Os números já temos de outra fonte. Sua função é capturar o que o TEXTO afirma: direção, intensidade, nível de alerta, sorotipos, ações de controle e avisos. Uma linha de sinal só existe quando o boletim faz uma AFIRMAÇÃO QUALITATIVA sobre um par (doença × local).

## Regras de emissão de linhas (`signals`)

- Emita uma linha SOMENTE para locais que o boletim DESTACA com uma afirmação qualitativa (tendência, alerta, comparação, sorotipo, intervenção).
- NÃO emita uma linha cujo único conteúdo seja um número. Local citado apenas com contagem, sem juízo qualitativo → IGNORE (ou no máximo registre em `primary_focus_locations`).
- Máximo de ~8 linhas. Priorize Brasil quando sinal de fato se aplicar ao território nacional + poucas UFs/regiões realmente destacadas.
- Na dúvida sobre um campo, use `nao_informado` / `false` / `null`. Nunca invente.

## O que NÃO fazer

- Não enumere todos os estados nem todas as semanas. Saliência, não exaustividade.
- Não retorne texto fora do JSON.

## Exemplo 1

TEXTO (trecho):
"Na SE 12 de 2024, o Brasil registrou crescimento expressivo de casos prováveis de dengue, com incidência muito acima do esperado para o período; o Ministério da Saúde reforça a campanha de vacinação (Qdenga) e o controle vetorial. Em Minas Gerais predomina o sorotipo DENV-3, recentemente reintroduzido, com tendência de crescimento e situação de emergência em diversos municípios. No Paraná foram notificados 18.430 casos prováveis. A chikungunya permanece estável no país."
SAÍDA:
```json
{
  "diseases_covered": ["dengue", "chikungunya"],
  "reference_year": 2024,
  "epi_week_end": 12,
  "overall_concern": "emergencia",
  "primary_focus_locations": ["Brasil", "Minas Gerais"],
  "signals": [
    {
      "disease": "dengue", "location_name": "Brasil", "location_level": "nacional",
      "epi_week_ref": 12, "trend": "forte_alta", "severity": "nao_informado",
      "serotypes_mentioned": [], "new_or_predominant_serotype": null,
      "interventions": ["vacinacao", "controle_vetorial"]
    },
    {
      "disease": "dengue", "location_name": "Minas Gerais", "location_level": "estado",
      "epi_week_ref": 12, "trend": "alta", "severity": "emergencia",
      "serotypes_mentioned": ["DENV-3"], "new_or_predominant_serotype": "DENV-3",
      "interventions": ["declaracao_emergencia"]
    },
    {
      "disease": "chikungunya", "location_name": "Brasil", "location_level": "nacional",
      "epi_week_ref": 12, "trend": "estavel", "severity": "nao_informado",
      "serotypes_mentioned": [], "new_or_predominant_serotype": null,
      "interventions": []
    }
  ]
}
```
Observe: o Paraná foi IGNORADO (só um número, sem juízo qualitativo). Esse é o comportamento correto.

## Exemplo 2

TEXTO (trecho):
"Em 2022 ocorreram 9.318 casos graves de dengue até a SE 20, com óbitos registrados. Em
9 de maio de 2022 foi instalada a Sala de Situação Nacional de Arboviroses Urbanas, com o
objetivo de reduzir casos graves e evitar óbitos."
```json
{
  "diseases_covered": ["dengue"],
  "reference_year": 2022,
  "epi_week_end": 20,
  "overall_concern": "atencao",
  "primary_focus_locations": ["Brasil"],
  "signals": [
    {
      "disease": "dengue", "location_name": "Brasil", "location_level": "nacional",
      "epi_week_ref": 20, "trend": "indefinido", "severity": "grave",
      "serotypes_mentioned": [], "new_or_predominant_serotype": null,
      "interventions": ["intensificacao_vigilancia"]
    }
  ]
}
```
Por quê: a ênfase em casos graves e óbitos define `severity: grave`; o texto não afirma direção de casos → `trend: indefinido`; a Sala de Situação é uma estrutura de vigilância coordenada → `intensificacao_vigilancia`.

## Exemplo 3

TEXTO (trecho):
"O DENV-2 foi o sorotipo predominante em 51,8% das amostras no país. Os estados com
circulação concomitante de DENV-1 e DENV-2 incluem São Paulo e Minas Gerais. O DENV-3 foi
detectado de forma concomitante ao DENV-1 no estado da Bahia."
```json
{
  "diseases_covered": ["dengue"],
  "reference_year": null,
  "epi_week_end": null,
  "overall_concern": "nao_informado",
  "primary_focus_locations": ["Brasil", "São Paulo", "Minas Gerais", "Bahia"],
  "signals": [
    {
      "disease": "dengue", "location_name": "Brasil", "location_level": "nacional",
      "epi_week_ref": null, "trend": "indefinido", "severity": "nao_informado",
      "serotypes_mentioned": ["DENV-2"], "new_or_predominant_serotype": "DENV-2",
      "interventions": []
    },
    {
      "disease": "dengue", "location_name": "São Paulo", "location_level": "estado",
      "epi_week_ref": null, "trend": "indefinido", "severity": "nao_informado",
      "serotypes_mentioned": ["DENV-1", "DENV-2"], "new_or_predominant_serotype": null,
      "interventions": []
    },
    {
      "disease": "dengue", "location_name": "Minas Gerais", "location_level": "estado",
      "epi_week_ref": null, "trend": "indefinido", "severity": "nao_informado",
      "serotypes_mentioned": ["DENV-1", "DENV-2"], "new_or_predominant_serotype": null,
      "interventions": []
    },
    {
      "disease": "dengue", "location_name": "Bahia", "location_level": "estado",
      "epi_week_ref": null, "trend": "indefinido", "severity": "nao_informado",
      "serotypes_mentioned": ["DENV-1", "DENV-3"], "new_or_predominant_serotype": "DENV-3",
      "interventions": []
    }
  ]
}
```
Por quê: cada estado nomeado com uma afirmação específica de sorotipo ganha sua própria linha —
São Paulo e Minas Gerais são DUAS linhas, não uma. O nacional registra apenas DENV-2 (único citado
no nível país) como predominante. A Bahia traz DENV-3 recém-detectado ao lado de DENV-1 →
`new_or_predominant_serotype: DENV-3`. Nenhum dos estados afirma direção de casos → `trend:
indefinido`.