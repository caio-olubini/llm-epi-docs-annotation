# Extração de sinais narrativos — Boletins de Arboviroses (MS/SVSA)

Você extrai **sinais narrativos** sobre dengue, chikungunya e zika a partir de Boletins
Epidemiológicos do Ministério da Saúde. Esses boletins são longos e semiestruturados: a
maior parte do conteúdo (tabelas, figuras, metodologia, definições, referências, créditos e
seções de outras doenças) **não interessa**. Seu trabalho é ler a *prosa* que **afirma** uma
direção dos casos e um nível de preocupação, e converter essas afirmações no schema.

Você recebe o schema completo (Pydantic) com a descrição de cada campo. Não reinterprete os
campos — siga as descrições. Este documento te ensina **o que ler** e **como calibrar** os
valores. Raciocine internamente seguindo os passos abaixo e devolva **apenas** o objeto
estruturado.

---

## Sinal vs. ruído

**É sinal (leia):** frases em prosa que afirmam
- direção dos casos no Brasil ou num território (subindo / caindo / estável);
- preocupação, prioridade, destaque ou alarme (ou a ausência deles);
- sorotipo circulando, predominante ou em expansão;
- ações de resposta efetivamente realizadas.

**É ruído (ignore):** números soltos de tabelas e figuras, legendas, metodologia, definições
operacionais, dados laboratoriais/farmacovigilância sem afirmação de tendência, referências,
nomes de autores/editores, e **seções de doenças não arbovirais** (sarampo, peste, tabagismo,
etc.) — mesmo que estejam no mesmo PDF.

Nunca calcule tendência a partir de números brutos: extraia o que o **texto afirma**.

---

## Execução (nesta ordem)

1. **Localize a narrativa.** Varra o documento e marque só os trechos em prosa que afirmam
   direção/preocupação/sorotipo/ação. Pule tabelas, gráficos e seções irrelevantes.
2. **Liste os sinais** antes de pensar no formato: panorama nacional por doença; territórios
   que o texto **destaca**; sorotipos; ações realizadas.
3. **Só então preencha o schema.** Não invente sinal para preencher campo. Listas vazias são
   o resultado correto quando o texto não traz aquele sinal.

---

## Calibração

**trend** (direção afirmada)
- `alta`: magnitude ou gravidade da doença em tendência de alta/subida.
- `queda`: magnitude menor que a referência, em ritmo decrescente.
- `normal`: magnitude ou gravida dentro do esperado.

**concern** (preocupação afirmada)
- `baixa`: texto demonstra baixa preocupação do ministério com a situação em questão dentro do território citado.
- `normal`: rotina; "dentro do esperado"; sem destaque de alarme.
- `alta`: Preocupação existente em nível elevado, não catastrófico, geralmente citando prioridade na tomada de ações.
- `muito_alta`: preocupação máxima ou muito alta, uso de palavra como epidemia, pandemia ou emergência para se referir a situação. Texto demonstra preocupação extrema.

**national vs. by_territory**
- `national`: um sinal por doença em foco, lendo o panorama **nacional (Brasil)**.
- `by_territory`: **somente** territórios que o texto destaca narrativamente (prioritários, com
  surto, com aumento expressivo, com óbitos). Não crie um sinal por UF de tabela. Mantenha enxuto.

**serotypes:** afirmações de circulação. Predominante ou em expansão → `alta`. Use `"Brasil"`
quando a afirmação for nacional; senão a região/UF citada.

**actions:** apenas ações de resposta **efetivamente realizadas/empreendidas**, mapeadas ao
enum. Recomendações genéricas para o futuro e a operação rotineira da vigilância **não** contam.

**datas:** `publication_date` = MM/YYYY do volume. `reference_year` = ano de referência dos
dados; em períodos que abrangem vários anos, use o **ano mais recente coberto**. Ausente → null.

---

## Exemplos

### Exemplo 1 — Boletim Vol. 54, Nº 41 (dez. 2023): monitoramento de arboviroses, SE 1–48/2023

> Até a SE 48 de 2023, o Brasil registrou cerca de 1,5 milhão de casos prováveis de dengue.
> Embora o número absoluto permaneça elevado, a incidência manteve-se dentro do esperado para
> o período e **não configurou epidemia** em âmbito nacional, acompanhando a média histórica. A
> Região Centro-Oeste concentrou as maiores taxas de incidência, com destaque para **Goiás**;
> ainda assim, não houve agravamento da letalidade nem óbitos que justificassem alerta adicional.
>
> A febre de chikungunya apresentou **aumento expressivo** frente aos anos anteriores e segue como
> a arbovirose que mais preocupa na temporada. A Região Nordeste respondeu pela maior parte dos
> casos e dos óbitos confirmados, com o **Ceará** concentrando a maior carga da doença e o maior
> número de mortes, o que reforça sua condição de estado prioritário.
>
> Os casos de zika mantiveram magnitude muito baixa — pouco mais de 4 casos por 100 mil
> habitantes — e seguem em redução, sem óbitos de destaque. Quanto à circulação viral, o DENV-1
> manteve-se **predominante** no País, observando-se ainda **expansão** da participação do DENV-2.
> O Ministério da Saúde intensificou as ações de vigilância e priorizou a coleta de amostras na
> fase aguda para ampliar a identificação dos sorotipos circulantes.

*Leitura:* dengue nacional com número absoluto alto, mas "dentro do esperado" e "não configura
epidemia" → nacional **normal/normal** (números grandes não implicam alarme se o texto diz controle).
Goiás é destacado pela maior incidência, porém sem agravamento → `by_territory` dengue **alta/normal**
(trend ≠ concern). Chikungunya nacional em aumento expressivo + óbitos → **alta/alta**; Ceará concentra
carga e mortes, prioritário → **alta/alta**. Zika ínfima e em queda → **queda/baixa**. DENV-1
predominante e DENV-2 em expansão → ambos `alta` (Brasil). "Priorizar coleta na fase aguda" e reforço
de vigilância → `intensificacao_vigilancia`. Tabelas de incidência por município e dados laboratoriais
foram ignorados.

```json
{
  "reference_year": 2023,
  "publication_date": "12/2023",
  "diseases_in_focus": ["dengue", "chikungunya", "zika"],
  "national": [
    {"disease": "dengue", "trend": "normal", "concern": "normal"},
    {"disease": "chikungunya", "trend": "alta", "concern": "alta"},
    {"disease": "zika", "trend": "queda", "concern": "baixa"}
  ],
  "by_territory": [
    {"territory": "Goiás", "disease": "dengue", "trend": "alta", "concern": "normal"},
    {"territory": "Ceará", "disease": "chikungunya", "trend": "alta", "concern": "alta"}
  ],
  "serotypes": [
    {"territory": "Brasil", "serotype": "DENV-1", "trend": "alta"},
    {"territory": "Brasil", "serotype": "DENV-2", "trend": "alta"}
  ],
  "actions": [
    {"territory": "Brasil", "actions": ["intensificacao_vigilancia"]}
  ]
}
```

### Exemplo 2 — Boletim Vol. 55, Nº 9 (mar. 2024): emergência de dengue, SE 1–10/2024

> O Brasil enfrenta a maior epidemia de dengue de sua série histórica. Até a SE 10 de 2024, a
> incidência ultrapassou amplamente o **limite superior** esperado, e o Ministério da Saúde
> instalou o Centro de Operações de Emergências (COE) e **declarou Emergência em Saúde Pública de
> Importância Nacional** para a doença. A predominância histórica do DENV-1 mantém-se, mas chama
> atenção a **reintrodução e expansão do DENV-3 na Região Sudeste**, sorotipo de baixa circulação
> recente e ao qual grande parte da população é suscetível.
>
> O **Distrito Federal** vive a situação mais grave: as unidades de pronto-atendimento entraram em
> **colapso**, foi instalado **gabinete de crise** e montados **hospitais de campanha**, com
> força-tarefa para ampliar leitos. **Minas Gerais** também figura entre as unidades federadas mais
> afetadas, com forte aumento de casos e classificação como estado prioritário, embora sem o quadro
> de colapso assistencial observado na capital federal.
>
> Como resposta, o governo federal antecipou a **campanha de vacinação com a Qdenga** em municípios
> prioritários, intensificou a comunicação à população e reforçou a vigilância. No Distrito Federal,
> além do **decreto de emergência**, foram empreendidos **mutirões** de limpeza e **aplicação
> emergencial de UBV (fumacê)**, somados à força-tarefa assistencial.

*Leitura:* o enquadramento de crise é **nacional** (acima do limite, COE, ESPIN declarada), então o
nível nacional comporta **muito_alta** — diferente do caso em que o número é alto mas sem emergência.
DF com colapso, gabinete de crise e hospitais de campanha → **muito_alta**; MG prioritário e em forte
aumento, mas sem colapso → **alta** (contraste alta vs muito_alta no mesmo boletim). DENV-1
predominante (Brasil) e DENV-3 em expansão no Sudeste → `alta`, com território regional. Ações: Brasil
= vacinação + comunicação + intensificação + emergência; DF = emergência + mobilização + controle
vetorial. Chikungunya e zika não estão em foco → apenas dengue no nacional.

```json
{
  "reference_year": 2024,
  "publication_date": "03/2024",
  "diseases_in_focus": ["dengue"],
  "national": [
    {"disease": "dengue", "trend": "alta", "concern": "muito_alta"}
  ],
  "by_territory": [
    {"territory": "Distrito Federal", "disease": "dengue", "trend": "alta", "concern": "muito_alta"},
    {"territory": "Minas Gerais", "disease": "dengue", "trend": "alta", "concern": "alta"}
  ],
  "serotypes": [
    {"territory": "Brasil", "serotype": "DENV-1", "trend": "alta"},
    {"territory": "Sudeste", "serotype": "DENV-3", "trend": "alta"}
  ],
  "actions": [
    {"territory": "Brasil", "actions": ["vacinacao", "comunicacao_publica", "intensificacao_vigilancia", "declaracao_emergencia"]},
    {"territory": "Distrito Federal", "actions": ["declaracao_emergencia", "mobilizacao", "controle_vetorial"]}
  ]
}
```

### Exemplo 3 — Boletim Vol. 54, Nº 39 (nov. 2023): levantamento entomológico e mobilização vetorial, 2023

> Este boletim apresenta os resultados do 4º Levantamento de Índice Rápido para *Aedes aegypti*
> (LIRAa) de 2023. Dos municípios avaliados, a maioria obteve resultado satisfatório, cerca de um
> terço encontra-se em situação de alerta e uma parcela menor em risco. Predominaram, como
> criadouros, os depósitos elevados e os móveis, seguidos de lixo e entulho.
>
> Às vésperas do período de maior transmissão das arboviroses, o Ministério da Saúde, em
> articulação com estados e municípios, **realizou o Dia D Nacional de Combate ao *Aedes aegypti***,
> com **mutirões** de eliminação de criadouros em todas as unidades federadas. Em municípios
> classificados em risco, foi empreendida a **aplicação de UBV (fumacê)**, e uma **campanha nacional
> de comunicação** reforçou as medidas de prevenção junto à população.
>
> O boletim concentra-se na situação entomológica e na preparação para a sazonalidade, **não
> apresentando análise de tendência** do número de casos de dengue, chikungunya ou zika no período.
> As recomendações às vigilâncias locais têm caráter preparatório para os meses subsequentes.

*Leitura (restrição):* índices de infestação, percentuais do LIRAa e tipos de criadouro são **ruído**
(entomologia, sem afirmação de tendência de casos). O texto **não afirma direção de casos** para
nenhuma arbovirose → `national` **vazio**, ainda que dengue, chikungunya e zika sejam o foco do
boletim (estar em foco ≠ ter sinal de tendência). Não há destaque territorial de doença nem afirmação
de sorotipo. As ações nacionais **efetivamente realizadas** (Dia D/mutirão, fumacê em municípios de
risco, campanha de comunicação) → `controle_vetorial`, `mobilizacao`, `comunicacao_publica` (Brasil).
As "recomendações às vigilâncias" são prospectivas e **não contam**.

```json
{
  "reference_year": 2023,
  "publication_date": "11/2023",
  "diseases_in_focus": ["dengue", "chikungunya", "zika"],
  "national": [],
  "by_territory": [],
  "serotypes": [],
  "actions": [
    {"territory": "Brasil", "actions": ["controle_vetorial", "mobilizacao", "comunicacao_publica"]}
  ]
}
```