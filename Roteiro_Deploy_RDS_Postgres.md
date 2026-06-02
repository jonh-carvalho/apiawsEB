# Roteiro de Deploy — Django REST API no AWS Elastic Beanstalk + RDS PostgreSQL + S3

**Disciplina:** Introdução ao Cloud Computing  
**Ambiente:** Console AWS (upload via app.zip)  
**Tempo estimado:** 50–70 minutos

---

## Visão Geral da Arquitetura

```
Internet
   │
   ▼
[Elastic Beanstalk]  ←── app.zip (código Python/Django)
   │  (EC2 + Load Balancer gerenciados pela AWS)
   │               │
   ▼               ▼
[RDS PostgreSQL] [S3 Bucket]
banco de dados   imagens dos produtos
(JSONB nativo)
```

**O que cada serviço faz:**
- **Elastic Beanstalk (EB):** gerencia automaticamente a infraestrutura (EC2, balanceador, auto scaling). Você só sobe o código.
- **RDS PostgreSQL:** banco relacional gerenciado com suporte nativo a **JSONB** — permite armazenar e consultar campos JSON diretamente no banco sem colunas extras.
- **S3:** armazenamento de objetos — guarda as imagens dos produtos de forma durável e escalável.

---

## Pré-requisitos

- Conta AWS Academy (ou conta própria) ativa
- Acesso ao Console AWS: [https://console.aws.amazon.com](https://console.aws.amazon.com)
- Arquivo `apps3.zip` gerado (instruções no **Passo 0**)

---

## Passo 0 — Gerar o app.zip

Selecione **todos os arquivos e pastas** dentro da pasta do projeto e compacte-os:

```
apiawsEB/
├── .ebextensions/
│   └── django.config
├── .platform/
│   └── hooks/
│       └── predeploy/
│           └── 01_django_setup.sh   ← roda migrate + collectstatic no deploy
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/
│   ├── __init__.py
│   ├── migrations/
│   │   ├── 0001_initial.py
│   │   └── 0002_produto_imagem.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── manage.py
├── Procfile
└── requirements.txt
```

> ⚠️ **Atenção:** o `manage.py` deve estar na **raiz** do zip, não dentro de uma subpasta.  
> Use **`git archive`** para gerar o zip — ele inclui apenas os arquivos rastreados pelo git, excluindo automaticamente `__pycache__`, `.venv` e `db.sqlite3`.

### Como zipar no Windows (PowerShell):
```powershell
cd f:\IbmecRepos\26.1\All\apiawsEB
git archive --format=zip HEAD -o apps3.zip
```

### Como zipar no Mac/Linux (Terminal):
```bash
cd /caminho/para/apiawsEB
git archive --format=zip HEAD -o apps3.zip
```

---

## Parte 1 — Criar o Banco de Dados RDS PostgreSQL

> **Por que PostgreSQL?** O Django usa `models.JSONField` para os campos `atributos` e `tags`.
> No PostgreSQL, esse campo é armazenado como **JSONB** — um tipo binário indexável que permite
> consultas como `produto__atributos__voltagem="220V"` direto no ORM, sem precisar de colunas extras.

### 1.1 Acessar o serviço RDS

1. No Console AWS, clique na barra de busca e digite **RDS**
2. Clique em **Amazon RDS**
3. Clique em **Criar banco de dados**

### 1.2 Configurar o banco

| Campo | Valor |
|---|---|
| Método de criação | Criação padrão |
| Tipo de mecanismo | **PostgreSQL** |
| Versão | PostgreSQL 16.x (mais recente disponível) |
| Modelos | **Nível gratuito** |
| Identificador | `db-produtos` |
| Nome do usuário principal | `admin` |
| Senha | `123456` (anote!) |
| Classe da instância | db.t3.micro |
| Armazenamento | 20 GB (padrão) |
| Conectividade → Acesso público | **Sim** (para facilitar o lab) |
| Nome do banco inicial | `produtos_db` |

4. Deixe os demais campos no padrão e clique em **Criar banco de dados**

> ⏳ A criação leva de 5 a 10 minutos. Continue para a Parte 1.5 enquanto aguarda.

### 1.3 Anotar o Endpoint do RDS

Após o banco ficar com status **Disponível**:
1. Clique no banco `db-produtos`
2. Na seção **Conectividade e segurança**, copie o **Endpoint**
3. Exemplo: `db-produtos.abc123xyz.us-east-1.rds.amazonaws.com`

---

## Parte 1.5 — Criar o Bucket S3 para Imagens

### 1.5.1 Criar o bucket

1. Na barra de busca, digite **S3** e clique em **Amazon S3**
2. Clique em **Criar bucket**

| Campo | Valor |
|---|---|
| Nome do bucket | `produtos-imagens-SEUNOME` (ex: `produtos-imagens-joao`) — deve ser **globalmente único** |
| Região | `us-east-1` (a mesma do RDS e EB) |
| Propriedade de objetos | `ACLs habilitadas` → selecione **Proprietário do bucket preferido** |
| Bloquear todo o acesso público | **Desmarque** esta opção |
| Confirmar desbloqueio | Marque a caixa de confirmação |

3. Deixe os demais campos no padrão e clique em **Criar bucket**

### 1.5.2 Configurar permissão de leitura pública

1. Clique no bucket recém-criado
2. Vá na aba **Permissões**
3. Na seção **Política do bucket**, clique em **Editar** e cole o JSON abaixo  
   (substitua `produtos-imagens-SEUNOME` pelo nome real do seu bucket):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadImages",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::produtos-imagens-SEUNOME/*"
        }
    ]
}
```

4. Clique em **Salvar alterações**

### 1.5.3 Adicionar permissão S3 ao perfil do EB

O Elastic Beanstalk roda em instâncias EC2 que usam uma **função IAM (role)** para acessar outros serviços da AWS. Precisamos dar acesso S3 a essa role.

1. Na barra de busca, digite **IAM** e clique em **IAM**
2. No menu lateral, clique em **Funções (Roles)**
3. Pesquise por `aws-elasticbeanstalk-ec2-role` e clique nela
4. Clique em **Adicionar permissões** → **Anexar políticas**
5. Pesquise por `AmazonS3FullAccess`, marque a caixa e clique em **Adicionar permissões**

> **Por que isso?** O código Django usa `boto3` para enviar arquivos ao S3. O boto3 dentro do EB usa automaticamente as credenciais da role EC2 — sem precisar de access keys no código.

### 1.5.4 Anotar o nome do bucket

Anote o nome do bucket criado:  
**Bucket:** `produtos-imagens-SEUNOME`

---

## Parte 1.6 — Entendendo o JSONField (JSONB) no Modelo

O modelo `Produto` possui dois campos que usam `models.JSONField` do Django:

```python
# api/models.py
atributos = models.JSONField(blank=True, default=dict)
# armazena especificações técnicas dinâmicas por categoria
# ex: {"cor": "preto", "voltagem": "bivolt", "garantia_anos": 2}

tags = models.JSONField(blank=True, default=list)
# armazena lista de palavras-chave (ou lista de objetos)
# ex: ["eletrônico", "promoção"] ou [{"nome": "promoção", "prioridade": 1}]
```

### Por que PostgreSQL + JSONB?

| Recurso | SQLite | MySQL (JSON) | PostgreSQL (JSONB) |
|---|---|---|---|
| Armazena JSON | ✅ (como texto) | ✅ (como texto) | ✅ (binário indexado) |
| Índices sobre campos JSON | ❌ | ❌ | ✅ (`GIN index`) |
| Consulta ORM por chave aninhada | ❌ | ❌ | ✅ |
| `django.db.models.JSONField` nativo | ✅ (sem índice) | ✅ (sem índice) | ✅ (com índice JSONB) |

**Exemplo de consulta ORM com JSONB (não precisa escrever SQL):**
```python
# Filtrar produtos com voltagem "220V"
Produto.objects.filter(atributos__voltagem="220V")

# Filtrar produtos com garantia maior que 1 ano
Produto.objects.filter(atributos__garantia_anos__gt=1)
```

### Estrutura esperada dos campos

**`atributos`** — objeto JSON (chave-valor livre, varia por categoria):
```json
{
    "cor": "preto",
    "voltagem": "bivolt",
    "peso_kg": 1.8,
    "garantia_anos": 2,
    "dimensoes": {"largura_cm": 35, "altura_cm": 2, "profundidade_cm": 25}
}
```

**`tags`** — array de objetos JSON (para categorização com metadados):
```json
[
    {"nome": "eletrônico", "prioridade": 1},
    {"nome": "promoção",   "prioridade": 2},
    {"nome": "novo",       "prioridade": 3}
]
```

> 💡 O campo `tags` aceita tanto array simples `["eletrônico", "novo"]` quanto array de objetos.
> Use array de objetos quando precisar de metadados extras (prioridade, cor de exibição, etc.).

---

## Parte 2 — Criar o Ambiente Elastic Beanstalk

### 2.1 Acessar o serviço

1. Na barra de busca, digite **Elastic Beanstalk**
2. Clique em **Elastic Beanstalk**
3. Clique em **Criar aplicação**

### 2.2 Configurar a aplicação

**Etapa 1 — Informações do ambiente:**

| Campo | Valor |
|---|---|
| Nome da aplicação | `api-produtos` |
| Nome do ambiente | `api-produtos-env` |
| Domínio | (deixe o padrão gerado) |
| Plataforma | **Python** |
| Versão da plataforma | Python 3.11 (ou a mais recente) |
| Código da aplicação | **Fazer upload do código** |
| Rótulo da versão | `v1` |

**Upload do código:**
1. Selecione **Arquivo local**
2. Clique em **Escolher arquivo** e selecione o `apps3.zip`
3. Clique em **Próximo**

### 2.3 Configurar acesso ao serviço

**Etapa 2 — Configurar acesso ao serviço:**

| Campo | Valor |
|---|---|
| Perfil de instância de serviço | `aws-elasticbeanstalk-ec2-role` |
| Par de chaves EC2 | (pode deixar em branco para o lab) |

> Se `aws-elasticbeanstalk-ec2-role` não aparecer, selecione **Criar e usar nova função de serviço** e mantenha o padrão.

Clique em **Próximo**.

### 2.4 Configurar rede, banco de dados e tags

**Etapa 3 — Configurar rede:**
- Deixe tudo no padrão (VPC padrão)
- Clique em **Próximo**

**Etapa 4 — Configurar instâncias e escalabilidade:**
- Tipo de instância: **t3.micro** (ou t2.micro)
- Clique em **Próximo**

**Etapa 5 — Configurar atualizações, monitoramento e registro em log:**

> ⚠️ **IMPORTANTE — Configure as variáveis de ambiente AQUI, antes de criar o ambiente!**
> Isso garante que o banco de dados seja criado corretamente durante o primeiro deploy.

Role a página até encontrar a seção **Propriedades do ambiente** e clique em **Adicionar propriedade de ambiente**.
Adicione as 6 variáveis abaixo (uma por vez, clicando no + a cada nova):

| Nome da variável | Valor |
|---|---|
| `RDS_HOSTNAME` | ← endpoint copiado no Passo 1.3 (ex: `db-produtos.abc123.us-east-1.rds.amazonaws.com`) |
| `RDS_PORT` | `5432` |
| `RDS_DB_NAME` | `produtos_db` |
| `RDS_USERNAME` | `admin` |
| `RDS_PASSWORD` | `123456` |
| `AWS_STORAGE_BUCKET_NAME` | ← nome do bucket (ex: `produtos-imagens-joao`) |
| `AWS_S3_REGION_NAME` | `us-east-1` |
| `DJANGO_DEBUG` | `False` |

Depois de adicionar todas as variáveis, clique em **Próximo**.

**Etapa 6 — Revisão** → Clique em **Enviar**

> ⏳ O EB levará de 5 a 10 minutos para provisionar o ambiente.  
> As variáveis já estarão disponíveis no primeiro deploy, então o banco de dados será criado automaticamente.

---

## Parte 3 — Verificar as Variáveis de Ambiente (Conferência)

Se precisar corrigir ou adicionar variáveis após a criação:

1. No Elastic Beanstalk, acesse **Ambientes** → `api-produtos-env`
2. No menu lateral esquerdo, clique em **Configuração**
3. Procure a seção **Propriedades do ambiente** e clique em **Editar**
4. Corrija os valores e clique em **Aplicar**
5. Após aplicar → no painel do ambiente, clique em **Fazer upload e implantar** e suba o mesmo `apps3.zip` novamente para forçar a re-execução das migrações

> **Por que re-deploy?** O `migrate` só roda durante o deploy. Se você corrigiu as variáveis após o primeiro deploy, é necessário fazer um novo upload para o migrate rodar com as variáveis corretas.

---

## Parte 4 — Verificar o Deploy

### 4.1 Confirmar que está no ar

1. No painel do ambiente EB, verifique o status: deve aparecer **Ok** (verde)
2. Clique na URL do ambiente (ex: `http://api-produtos-env.eba-xxxx.us-east-1.elasticbeanstalk.com`)

### 4.2 Testar os endpoints

Use o navegador ou um cliente HTTP (Postman, Insomnia, `curl`):

**Verificar saúde da API:**
```
GET http://<sua-url>/api/health/
```
Resposta esperada:
```json
{"status": "ok", "mensagem": "API funcionando!"}
```

**Listar produtos (vazio no início):**
```
GET http://<sua-url>/api/produtos/
```

**Criar um produto (sem imagem) — apenas campos básicos:**
```
POST http://<sua-url>/api/produtos/
Content-Type: application/json

{
    "nome": "Notebook Dell",
    "descricao": "Notebook i7, 16GB RAM, 512GB SSD",
    "preco": "3999.90",
    "estoque": 10
}
```

**Criar um produto COM campos JSONB — `atributos` e `tags`:**
```
POST http://<sua-url>/api/produtos/
Content-Type: application/json

{
    "nome": "Notebook Dell XPS 15",
    "descricao": "Notebook para desenvolvimento com OLED 4K",
    "preco": "8999.90",
    "estoque": 5,
    "atributos": {
        "cor": "prata",
        "processador": "Intel Core i7-13700H",
        "ram_gb": 32,
        "ssd_gb": 1024,
        "tela_polegadas": 15.6,
        "voltagem": "bivolt",
        "garantia_anos": 2,
        "dimensoes": {
            "largura_cm": 34.4,
            "altura_cm": 1.86,
            "profundidade_cm": 23.5
        }
    },
    "tags": [
        {"nome": "eletrônico",   "prioridade": 1},
        {"nome": "notebook",     "prioridade": 1},
        {"nome": "promoção",     "prioridade": 2},
        {"nome": "lançamento",   "prioridade": 3}
    ]
}
```

Resposta esperada (status `201 Created`):
```json
{
    "id": 1,
    "nome": "Notebook Dell XPS 15",
    "descricao": "Notebook para desenvolvimento com OLED 4K",
    "preco": "8999.90",
    "estoque": 5,
    "imagem": null,
    "atributos": {
        "cor": "prata",
        "processador": "Intel Core i7-13700H",
        "ram_gb": 32,
        "ssd_gb": 1024,
        "tela_polegadas": 15.6,
        "voltagem": "bivolt",
        "garantia_anos": 2,
        "dimensoes": {
            "largura_cm": 34.4,
            "altura_cm": 1.86,
            "profundidade_cm": 23.5
        }
    },
    "tags": [
        {"nome": "eletrônico",   "prioridade": 1},
        {"nome": "notebook",     "prioridade": 1},
        {"nome": "promoção",     "prioridade": 2},
        {"nome": "lançamento",   "prioridade": 3}
    ],
    "criado_em": "2026-06-02T22:00:00Z",
    "atualizado_em": "2026-06-02T22:00:00Z"
}
```

> 💡 Os campos `atributos` e `tags` são **opcionais** — se omitidos, o padrão é `{}` e `[]` respectivamente.
> Você pode enviar qualquer estrutura JSON válida; o PostgreSQL armazena como JSONB e mantém os tipos nativos (número, booleano, objeto aninhado).

**Criar um produto COM imagem E campos JSONB (via Postman/Insomnia):**
```
POST http://<sua-url>/api/produtos/
Content-Type: multipart/form-data

nome                      = Smartphone Samsung Galaxy S25
descricao                 = Smartphone 5G com câmera de 200MP
preco                     = 4299.90
estoque                   = 20
imagem                    = [selecionar arquivo .jpg ou .png]
atributos                 = {"cor":"grafite","ram_gb":12,"armazenamento_gb":256,"voltagem":"bivolt","5g":true}
tags                      = [{"nome":"smartphone","prioridade":1},{"nome":"5g","prioridade":1},{"nome":"oferta","prioridade":2}]
```
> No Postman: aba **Body** → **form-data**. Para `atributos` e `tags`, mantenha o tipo como **Text** e cole o JSON como string — o Django REST Framework faz o parse automaticamente.

A resposta incluirá a URL pública do S3 e os campos JSONB:
```json
{
    "id": 2,
    "nome": "Smartphone Samsung Galaxy S25",
    "preco": "4299.90",
    "estoque": 20,
    "imagem": "https://produtos-imagens-joao.s3.amazonaws.com/produtos/galaxy.jpg",
    "atributos": {
        "cor": "grafite",
        "ram_gb": 12,
        "armazenamento_gb": 256,
        "voltagem": "bivolt",
        "5g": true
    },
    "tags": [
        {"nome": "smartphone", "prioridade": 1},
        {"nome": "5g",         "prioridade": 1},
        {"nome": "oferta",     "prioridade": 2}
    ],
    "criado_em": "2026-06-02T22:05:00Z",
    "atualizado_em": "2026-06-02T22:05:00Z"
}
```

**Listar novamente:**
```
GET http://<sua-url>/api/produtos/
```

**Buscar produto específico:**
```
GET http://<sua-url>/api/produtos/1/
```

**Atualizar produto:**
```
PUT http://<sua-url>/api/produtos/1/
Content-Type: application/json

{
    "nome": "Notebook Dell XPS",
    "descricao": "Notebook i9, 32GB RAM",
    "preco": "5999.90",
    "estoque": 5
}
```

**Deletar produto:**
```
DELETE http://<sua-url>/api/produtos/1/
```

---

## Parte 5 — Solução de Problemas

### Como obter os logs corretos

O bundle de logs padrão do EB **não inclui** os logs do gunicorn/Django. Para ver o erro real:

1. No EB, vá em **Logs** → **Solicitar logs** → **Últimas 100 linhas**
2. Baixe o arquivo `.zip` e abra o arquivo `var/log/web.stdout.log`
3. Esse arquivo contém o `Traceback` completo do erro Python

> O arquivo `var/log/nginx/healthd/application.log.*` mostra apenas os códigos HTTP (200, 404, 500), não a causa do erro.

### O ambiente está com status "Degradado" ou "Grave"

1. No EB, vá em **Logs** → **Solicitar logs** → **Últimas 100 linhas**
2. Baixe e abra o arquivo de log
3. Procure por linhas com `ERROR` ou `CRITICAL`

**Erros comuns:**

| Erro | Causa | Solução |
|---|---|---|
| `could not connect to server: Connection refused` | `RDS_HOSTNAME` errado ou RDS não acessível | Verifique o endpoint e o Security Group do RDS (porta 5432) |
| `password authentication failed for user "admin"` | Senha ou usuário errado | Confira `RDS_USERNAME` e `RDS_PASSWORD` |
| `database "produtos_db" does not exist` | Banco não criado | Verifique o nome do banco no RDS |
| `relation "api_produto" does not exist` | Variáveis RDS não estavam configuradas no deploy | Re-faça o upload do `app.zip` após configurar as variáveis |
| `ModuleNotFoundError: No module named 'psycopg2'` | Falta `psycopg2-binary` no requirements | Verifique o `requirements.txt` no zip |
| `Invalid HTTP_HOST header` | `ALLOWED_HOSTS` muito restrito | Verifique se está `['*']` no settings.py |
| HTTP 500 em `/api/` | collectstatic não rodou / staticfiles.json ausente | Re-faça o upload do `app.zip` para forçar novo deploy |
| `An error occurred (AccessDenied) when calling PutObject` | Role do EB sem permissão S3 | Adicione `AmazonS3FullAccess` ao `aws-elasticbeanstalk-ec2-role` |
| `NoSuchBucket` | Nome do bucket errado na variável | Verifique `AWS_STORAGE_BUCKET_NAME` no EB |
| Imagem salva mas URL retorna `Access Denied` | Bucket sem leitura pública | Revise a política do bucket (JSON do Passo 1.5.2) e desabilite "Bloquear acesso público" |
| `django.db.utils.ProgrammingError: column ... is of type jsonb` | Migração `0003_postgres_jsonfield` não rodou | Verifique o log do deploy; re-faça o upload do `app.zip` |

### Liberar o Security Group do RDS

Se o EB não consegue acessar o RDS:
1. Acesse **RDS** → `db-produtos` → **Conectividade e segurança**
2. Clique no Security Group do RDS
3. **Regras de entrada** → **Editar regras de entrada** → **Adicionar regra**:
   - Tipo: `PostgreSQL`
   - Porta: `5432`
   - Origem: `0.0.0.0/0` (para o lab)
4. Salvar regras

---

## Resumo dos Endpoints da API

| Método | URL | Ação |
|---|---|---|
| GET | `/api/health/` | Verifica se a API está no ar |
| GET | `/api/produtos/` | Lista todos os produtos |
| POST | `/api/produtos/` | Cria produto (JSON ou multipart com imagem) |
| GET | `/api/produtos/{id}/` | Detalhe de um produto |
| PUT | `/api/produtos/{id}/` | Atualiza produto (pode incluir nova imagem) |
| DELETE | `/api/produtos/{id}/` | Remove produto |

---

## Checklist Final

- [ ] RDS **PostgreSQL** criado com status **Disponível**
- [ ] Endpoint do RDS anotado
- [ ] Security Group do RDS liberado na porta **5432** para `0.0.0.0/0`
- [ ] Bucket S3 criado com leitura pública habilitada
- [ ] Política do bucket configurada (JSON colado e salvo)
- [ ] `AmazonS3FullAccess` adicionada ao `aws-elasticbeanstalk-ec2-role`
- [ ] `apps3.zip` gerado com `manage.py` na raiz (incluindo pastas `migrations/` e `.platform/`)
- [ ] Ambiente EB criado com plataforma **Python**
- [ ] Upload do `app.zip` realizado
- [ ] 8 variáveis de ambiente configuradas no EB (`RDS_PORT=5432`, bucket S3, etc.)
- [ ] Status do ambiente EB: **Ok** (verde)
- [ ] `GET /api/health/` retorna `{"status": "ok"}`
- [ ] Conseguiu criar um produto simples via `POST /api/produtos/`
- [ ] Conseguiu criar um produto com `atributos` (objeto JSON) e `tags` (array de objetos)
- [ ] Resposta JSON inclui `atributos` e `tags` corretamente retornados
- [ ] Conseguiu criar um produto COM imagem via `POST` multipart (com `atributos` e `tags` como texto JSON)
- [ ] URL da imagem no JSON aponta para o S3 (`https://seu-bucket.s3.amazonaws.com/...`)
- [ ] Imagem acessível pelo navegador via URL do S3

---

## Limpar os Recursos (ao final da aula)

> ⚠️ Para evitar cobranças, sempre encerre os recursos após o lab!

1. **Elastic Beanstalk:** Ações → **Encerrar ambiente**
2. **RDS:** Selecione o banco → **Ações** → **Excluir** (desmarque snapshot final para excluir mais rápido)
3. **S3:** Selecione o bucket → **Esvaziar** (deletar todos os objetos) → depois **Excluir bucket**

---

*Roteiro preparado para turma de Introdução ao Cloud Computing — IBMEC 2026.1*
