# Roteiro de Análise — JSONB no PostgreSQL com Django ORM

**Disciplina:** Introdução ao Cloud Computing  
**Branch:** `feature/jsonb-analise`  
**Tempo estimado:** 30–40 minutos

---

## Visão Geral

Este roteiro demonstra como o **PostgreSQL** armazena campos JSON como **JSONB** (binário indexado) e como o **Django ORM** permite consultar esses campos sem escrever SQL manualmente.

O modelo `Produto` possui dois campos JSONB:

| Campo | Tipo Python | Tipo PostgreSQL | Estrutura |
|---|---|---|---|
| `atributos` | `dict` | `jsonb` | objeto com especificações técnicas variáveis por categoria |
| `tags` | `list` | `jsonb` | array de objetos `{"nome": "...", "prioridade": N}` |

### Por que JSONB é diferente de JSON comum?

```
JSON (texto)          JSONB (binário)
─────────────────     ───────────────────────────────────────
Armazenado como       Convertido para formato binário
string de texto       indexável pelo PostgreSQL

Sem índices           Suporta índices GIN (busca dentro do JSON)

Sem filtros ORM       Filtros ORM nativos:
avançados               __has_key, __contains, __voltagem=X,
                        __garantia_anos__gte=2, __5g=True
```

---

## Pré-requisitos

- Ambiente EB configurado com RDS PostgreSQL (roteiro principal concluído)
- Variáveis `RDS_*` configuradas no Elastic Beanstalk
- `apps3.zip` gerado a partir da branch `feature/jsonb-analise`

---

## Passo 0 — Gerar o ZIP da branch de análise

No terminal local, mude para a branch de análise e gere o zip:

```powershell
cd f:\IbmecRepos\26.1\All\apiawsEB
git checkout feature/jsonb-analise
git archive --format=zip HEAD -o apps3_jsonb.zip
```

> O zip incluirá o management command `seed_produtos` e os novos endpoints de análise.

---

## Passo 1 — Fazer deploy no Elastic Beanstalk

1. No Console AWS, acesse **Elastic Beanstalk** → `api-produtos-env`
2. Clique em **Fazer upload e implantar**
3. Selecione o arquivo `apps3_jsonb.zip`
4. Rótulo da versão: `v2-jsonb`
5. Clique em **Implantar**

> ⏳ Aguarde o status voltar para **Ok** (verde).  
> O hook `.platform/hooks/predeploy/01_django_setup.sh` executa `python manage.py migrate` automaticamente — não há migração nova nesta branch, apenas código novo.

---

## Passo 2 — Carregar os Dados de Amostra

O management command `seed_produtos` insere **12 produtos** com campos JSONB ricos, cobrindo 5 categorias:

| Categoria | Produtos |
|---|---|
| Notebooks | Dell XPS 15, Lenovo IdeaPad 3 |
| Smartphones | Samsung Galaxy S25, Motorola Moto G54 |
| TVs | LG OLED 55", Samsung Crystal 50" |
| Eletrodomésticos | Geladeira Brastemp, Lavadora Consul, Ar Split Midea |
| Periféricos | Monitor LG UltraWide, Teclado Redragon, Mouse Logitech |

### 2.1 Executar o seed via SSH no EB

No Console AWS:

1. Acesse **Elastic Beanstalk** → `api-produtos-env`
2. No menu lateral, clique em **SSH** (ou use o **EC2 Instance Connect**)
3. No terminal da instância, execute:

```bash
# Ativar o ambiente virtual do Django no EB
source /var/app/venv/*/bin/activate
cd /var/app/current

# Inserir os produtos de amostra (idempotente — pode rodar várias vezes)
python manage.py seed_produtos

# Se quiser limpar e reinserir do zero:
python manage.py seed_produtos --limpar
```

Saída esperada:
```
Seed concluído: 12 produto(s) criado(s), 0 já existia(m).
```

### 2.2 Confirmar a carga via API

```
GET http://<sua-url>/api/produtos/
```

Deve retornar um array com 12 produtos, cada um com `atributos` e `tags` preenchidos.

---

## Passo 3 — Explorar os Endpoints de Análise JSONB

Todos os endpoints abaixo são `GET` e não requerem autenticação.  
Substitua `<sua-url>` pela URL do seu ambiente EB.

---

### Análise 1 — Painel Geral

```
GET http://<sua-url>/api/analise/resumo/
```

**O que faz:** visão consolidada do catálogo — total de produtos, preço mínimo/médio/máximo, estoque total, contagem de produtos 5G e distribuição de voltagem.

**Resposta esperada:**
```json
{
    "total_produtos": 12,
    "estoque_total_unidades": 371,
    "preco": {
        "minimo": "349.90",
        "maximo": "8999.90",
        "medio": "3019.82"
    },
    "produtos_com_5g": 2,
    "garantia_media_anos": "1.6",
    "distribuicao_voltagem": {
        "bivolt": 9,
        "220V": 3
    },
    "dica": "Use /api/analise/tags/, ..."
}
```

> 💡 **Conceito:** o campo `distribuicao_voltagem` foi calculado iterando sobre o JSONB de cada produto e extraindo `atributos['voltagem']` — sem uma coluna separada no banco.

---

### Análise 2 — Ranking de Tags

```
GET http://<sua-url>/api/analise/tags/
```

**O que faz:** conta quantos produtos possuem cada tag, ordenando do mais ao menos frequente.

**Técnica JSONB usada:**
```python
# Filtra produtos cujo campo 'tags' contém o objeto {"nome": "eletrônico"}
Produto.objects.filter(tags__contains=[{"nome": "eletrônico"}])
```

O operador `__contains` do PostgreSQL verifica se o array JSONB contém o elemento especificado. Funciona com objetos aninhados inteiros.

**Resposta esperada:**
```json
[
    {"tag": "eletrônico",     "total": 6},
    {"tag": "promoção",       "total": 4},
    {"tag": "lançamento",     "total": 3},
    {"tag": "premium",        "total": 3},
    {"tag": "custo-benefício","total": 2},
    ...
]
```

> 🔍 **Observe:** "eletrônico" aparece em notebooks, smartphones, TVs e periféricos — a tag conecta categorias diferentes sem precisar de uma tabela separada de relacionamento.

---

### Análise 3 — Agrupamento por Voltagem

```
GET http://<sua-url>/api/analise/voltagem/
```

**O que faz:** agrupa os produtos pela voltagem declarada no JSONB e calcula o preço médio de cada grupo.

**Técnica JSONB usada:**
```python
# Acessa a chave 'voltagem' dentro do objeto JSON 'atributos'
produto.atributos.get('voltagem')

# No ORM (filtro direto):
Produto.objects.filter(atributos__voltagem="bivolt")
```

A notação `atributos__voltagem` é traduzida pelo Django para o operador PostgreSQL `atributos->>'voltagem'`.

**Resposta esperada:**
```json
[
    {"voltagem": "bivolt", "total": 9, "preco_medio": "3061.01"},
    {"voltagem": "220V",   "total": 3, "preco_medio": "2399.90"}
]
```

> 💡 **Reflexão:** produtos bivolt tendem a ser mais caros (notebooks, smartphones premium). Produtos 220V são eletrodomésticos com preço médio menor nesta amostra.

---

### Análise 4 — Estatísticas de RAM

```
GET http://<sua-url>/api/analise/ram-notebooks/
```

**O que faz:** filtra apenas produtos que possuem o atributo `ram_gb` no JSONB (notebooks e smartphones) e compara RAM e preço.

**Técnica JSONB usada:**
```python
# __has_key verifica se a chave existe no objeto JSON
# sem precisar saber seu valor — apenas a presença da chave
Produto.objects.filter(atributos__has_key='ram_gb')
```

Isso é equivalente ao SQL PostgreSQL:
```sql
SELECT * FROM api_produto WHERE atributos ? 'ram_gb';
```

**Resposta esperada:**
```json
{
    "produtos_com_ram": 4,
    "ram_minima_gb": 8,
    "ram_maxima_gb": 32,
    "detalhes": [
        {"nome": "Notebook Dell XPS 15",   "ram_gb": 32, "processador": "Intel Core i7-13700H", "preco": "8999.90"},
        {"nome": "Notebook Lenovo IdeaPad","ram_gb": 8,  "processador": "AMD Ryzen 5 5500U",    "preco": "2799.90"},
        {"nome": "Smartphone Samsung S25", "ram_gb": 12, "processador": "Snapdragon 8 Gen 4",   "preco": "4299.90"},
        {"nome": "Smartphone Moto G54",    "ram_gb": 8,  "processador": "MediaTek Dimensity",   "preco": "1099.90"}
    ]
}
```

> 💡 **Ponto chave:** TVs, eletrodomésticos e periféricos **não aparecem** neste resultado, pois não têm a chave `ram_gb` no JSONB — sem precisar de uma coluna `categoria` separada.

---

### Análise 5 — Comparativo 5G

```
GET http://<sua-url>/api/analise/5g/
```

**O que faz:** separa produtos com e sem suporte 5G, filtrando pelo campo booleano dentro do JSONB.

**Técnica JSONB usada:**
```python
# Filtra pelo valor booleano dentro do objeto JSON
Produto.objects.filter(atributos__5g=True)

# O PostgreSQL armazena true/false como tipo booleano nativo dentro do JSONB
# — não como string "true" ou número 1
```

**Resposta esperada:**
```json
{
    "com_5g": {
        "total": 2,
        "preco_medio": "2699.90",
        "produtos": [
            {"nome": "Smartphone Motorola Moto G54",    "preco": "1099.90", "ram_gb": 8},
            {"nome": "Smartphone Samsung Galaxy S25",   "preco": "4299.90", "ram_gb": 12}
        ]
    },
    "sem_5g": {
        "total": 0,
        "preco_medio": null,
        "produtos": []
    }
}
```

> 💡 **Detalhe importante:** produtos sem o campo `5g` no JSONB (TVs, notebooks, eletrodomésticos) **não aparecem** em nenhum dos grupos — porque `__has_key='5g'` filtra apenas quem declarou o campo. Isso evita falsos negativos.

---

### Análise 6 — Agrupamento por Garantia

```
GET http://<sua-url>/api/analise/garantia/
```

**O que faz:** separa produtos por tempo de garantia usando filtros numéricos sobre o JSONB.

**Técnica JSONB usada:**
```python
# Filtro de comparação numérica diretamente sobre o valor JSON
Produto.objects.filter(atributos__garantia_anos__gte=2)   # >= 2 anos
Produto.objects.filter(atributos__garantia_anos=1)         # exatamente 1 ano
Produto.objects.exclude(atributos__has_key='garantia_anos')# sem info
```

O Django traduz `__garantia_anos__gte=2` para o SQL:
```sql
WHERE (atributos->>'garantia_anos')::numeric >= 2
```

**Resposta esperada:**
```json
{
    "garantia_2_anos_ou_mais": {
        "total": 5,
        "preco_medio": "4619.88",
        "produtos": [
            {"nome": "Notebook Dell XPS 15",        "preco": "8999.90", "garantia_anos": 2},
            {"nome": "Smart TV LG OLED 55\"",       "preco": "5499.90", "garantia_anos": 2},
            {"nome": "Monitor LG UltraWide 29\"",   "preco": "1599.90", "garantia_anos": 2},
            ...
        ]
    },
    "garantia_1_ano": {
        "total": 7,
        "preco_medio": "2091.34",
        "produtos": [...]
    },
    "sem_garantia_definida": {"total": 0}
}
```

> 💡 **Conclusão:** produtos com garantia de 2 anos têm preço médio ~2× maior do que os de 1 ano. Essa análise foi feita sem uma coluna `garantia_anos` na tabela — o valor vive dentro do JSONB.

---

## Passo 4 — Visualizar o JSONB no PostgreSQL (Opcional)

Se tiver acesso ao banco via `psql` ou DBeaver, execute as queries SQL equivalentes para ver o JSONB em ação:

```sql
-- Ver todos os atributos como JSON
SELECT nome, atributos FROM api_produto LIMIT 5;

-- Extrair campo específico do JSONB (operador ->>)
SELECT nome, atributos->>'voltagem' AS voltagem FROM api_produto;

-- Filtrar por valor dentro do JSONB
SELECT nome, preco FROM api_produto
WHERE atributos->>'garantia_anos' = '2';

-- Verificar existência de chave (operador ?)
SELECT nome FROM api_produto
WHERE atributos ? 'ram_gb';

-- Filtrar array de objetos com @> (contém)
SELECT nome FROM api_produto
WHERE tags @> '[{"nome": "promoção"}]';

-- Comparação numérica com cast
SELECT nome, (atributos->>'ram_gb')::int AS ram_gb
FROM api_produto
WHERE (atributos->>'ram_gb')::int >= 16
ORDER BY ram_gb DESC;
```

> 💡 O ORM do Django gera exatamente essas queries automaticamente quando você usa `__has_key`, `__contains` e `__campo__gte`.

---

## Resumo das Técnicas JSONB Demonstradas

| Endpoint | Operador Django ORM | Equivalente SQL PostgreSQL | Uso |
|---|---|---|---|
| `/analise/tags/` | `tags__contains=[{"nome": x}]` | `tags @> '[{"nome": x}]'` | Busca em array de objetos |
| `/analise/voltagem/` | `atributos__voltagem="bivolt"` | `atributos->>'voltagem' = 'bivolt'` | Filtro por valor de chave |
| `/analise/ram-notebooks/` | `atributos__has_key='ram_gb'` | `atributos ? 'ram_gb'` | Verifica presença de chave |
| `/analise/5g/` | `atributos__5g=True` | `(atributos->'5g')::bool = true` | Filtro booleano nativo |
| `/analise/garantia/` | `atributos__garantia_anos__gte=2` | `(atributos->>'garantia_anos')::numeric >= 2` | Comparação numérica |

---

## Checklist Final

- [ ] Deploy do `apps3_jsonb.zip` realizado com status **Ok**
- [ ] `python manage.py seed_produtos` executado com sucesso (12 produtos criados)
- [ ] `GET /api/produtos/` retorna 12 produtos com `atributos` e `tags` preenchidos
- [ ] `GET /api/analise/resumo/` retorna o painel geral
- [ ] `GET /api/analise/tags/` lista tags em ordem decrescente de frequência
- [ ] `GET /api/analise/voltagem/` mostra agrupamento por voltagem com preço médio
- [ ] `GET /api/analise/ram-notebooks/` lista apenas notebooks e smartphones (4 produtos)
- [ ] `GET /api/analise/5g/` separa produtos com e sem 5G
- [ ] `GET /api/analise/garantia/` separa produtos por tempo de garantia
- [ ] (Opcional) Queries SQL executadas diretamente no PostgreSQL via psql/DBeaver

---

## Questões para Reflexão

1. **Por que usar JSONB em vez de colunas separadas?**  
   Produtos de categorias diferentes têm atributos totalmente distintos (TVs têm `resolucao`, notebooks têm `ram_gb`, eletrodomésticos têm `capacidade_litros`). Com JSONB, um único modelo cobre todos sem `NULL` em dezenas de colunas.

2. **Qual a limitação do JSONB em relação a colunas normais?**  
   Joins e constraints (chave estrangeira, `NOT NULL`, `UNIQUE`) não se aplicam a campos dentro do JSONB. Para dados que precisam de integridade relacional, use colunas normais.

3. **Quando criar um índice GIN no campo JSONB?**  
   Quando o campo for frequentemente consultado com `__contains` ou `__has_key` em tabelas com muitos registros. O índice GIN permite ao PostgreSQL buscar dentro do JSON sem varredura completa da tabela.

---

*Roteiro preparado para turma de Introdução ao Cloud Computing — IBMEC 2026.1*
