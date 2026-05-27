# Django REST API no AWS Elastic Beanstalk + RDS MySQL

**Disciplina:** Big Data e Cloud Computing  
**Ambiente:** Console AWS (upload via app.zip)  
**Tempo estimado:** 40–60 minutos

---

## Visão Geral da Arquitetura

```
Internet
   │
   ▼
[Elastic Beanstalk]  ←── app.zip (código Python/Django)
   │  (EC2 + Load Balancer gerenciados pela AWS)
   │
   ▼
[RDS MySQL]          ←── banco de dados relacional gerenciado
```

**O que cada serviço faz:**
- **Elastic Beanstalk (EB):** gerencia automaticamente a infraestrutura (EC2, balanceador, auto scaling). Você só sobe o código.
- **RDS MySQL:** banco de dados gerenciado — sem instalar MySQL manualmente.

---

## Pré-requisitos

- Conta AWS Academy (ou conta própria) ativa
- Acesso ao Console AWS: [https://console.aws.amazon.com](https://console.aws.amazon.com)
- Arquivo `app.zip` gerado (instruções no **Passo 0**)

---

## Passo 0 — Gerar o app.zip

Selecione **todos os arquivos e pastas** dentro da pasta do projeto e compacte-os:

```
apiawsEB/
├── .ebextensions/
│   └── django.config
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── manage.py
├── Procfile
└── requirements.txt
```

> ⚠️ **Atenção:** o `manage.py` deve estar na **raiz** do zip, não dentro de uma subpasta.  
> Selecione todos os arquivos dentro da pasta e use "Enviar para → Pasta compactada" (Windows) ou `zip -r app.zip .` (terminal).

### Como zipar no Windows (PowerShell):
```powershell
cd f:\IbmecRepos\26.1\All\apiawsEB
Compress-Archive -Path * -DestinationPath ..\app.zip -Force
```

### Como zipar no Mac/Linux (Terminal):
```bash
cd /caminho/para/apiawsEB
zip -r ../app.zip . -x "*.pyc" -x "__pycache__/*" -x "db.sqlite3"
```

---

## Parte 1 — Criar o Banco de Dados RDS MySQL

### 1.1 Acessar o serviço RDS

1. No Console AWS, clique na barra de busca e digite **RDS**
2. Clique em **Amazon RDS**
3. Clique em **Criar banco de dados**

### 1.2 Configurar o banco

| Campo | Valor |
|---|---|
| Método de criação | Criação padrão |
| Tipo de mecanismo | **MySQL** |
| Versão | MySQL 8.0.x (mais recente disponível) |
| Modelos | **Nível gratuito** |
| Identificador | `db-produtos` |
| Nome do usuário principal | `admin` |
| Senha | `12345678` (anote!) |
| Classe da instância | db.t3.micro |
| Armazenamento | 20 GB (padrão) |
| Conectividade → Acesso público | **Sim** (para facilitar o lab) |
| Nome do banco inicial | `produtos_db` |

4. Deixe os demais campos no padrão e clique em **Criar banco de dados**

> ⏳ A criação leva de 5 a 10 minutos. Continue para a Parte 2 enquanto aguarda.

### 1.3 Anotar o Endpoint do RDS

Após o banco ficar com status **Disponível**:
1. Clique no banco `db-produtos`
2. Na seção **Conectividade e segurança**, copie o **Endpoint**
3. Exemplo: `db-produtos.abc123xyz.us-east-1.rds.amazonaws.com`

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
2. Clique em **Escolher arquivo** e selecione o `app.zip`
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
| `RDS_PORT` | `3306` |
| `RDS_DB_NAME` | `produtos_db` |
| `RDS_USERNAME` | `admin` |
| `RDS_PASSWORD` | `12345678` |
| `DJANGO_DEBUG` | `False` |

Depois de adicionar todas as variáveis, clique em **Próximo**.

#### 1. Security Group do RDS — liberar porta 3306
Antes de fazer o deploy:

RDS → db-produtos → Conectividade e segurança → clique no Security Group
Regras de entrada → Editar → Adicionar regra:
Tipo: MySQL/Aurora | Porta: 3306 | Origem: 0.0.0.0/0
Salvar

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
5. Após aplicar → no painel do ambiente, clique em **Fazer upload e implantar** e suba o mesmo `app.zip` novamente para forçar a re-execução das migrações

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

**Criar um produto:**
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
| `Can't connect to MySQL server` | Variável `RDS_HOSTNAME` errada ou RDS não acessível | Verifique o endpoint e o Security Group do RDS |
| `Access denied for user` | Senha ou usuário errado | Confira `RDS_USERNAME` e `RDS_PASSWORD` |
| `Unknown database 'produtos_db'` | Banco não criado | Verifique o nome do banco no RDS |
| `Table 'produtos_db.api_produto' doesn't exist` | Variáveis RDS não estavam configuradas no deploy | Re-faça o upload do `app.zip` após configurar as variáveis |
| `ModuleNotFoundError` | Falta de dependência | Verifique o `requirements.txt` no zip |
| `Invalid HTTP_HOST header` | `ALLOWED_HOSTS` muito restrito | Verifique se está `['*']` no settings.py |
| HTTP 500 em `/api/` | collectstatic não rodou / staticfiles.json ausente | Re-faça o upload do `app.zip` para forçar novo deploy |

### Liberar o Security Group do RDS

Se o EB não consegue acessar o RDS:
1. Acesse **RDS** → `db-produtos` → **Conectividade e segurança**
2. Clique no Security Group do RDS
3. **Regras de entrada** → **Editar regras de entrada** → **Adicionar regra**:
   - Tipo: `MySQL/Aurora`
   - Porta: `3306`
   - Origem: `0.0.0.0/0` (para o lab)
4. Salvar regras

---

## Resumo dos Endpoints da API

| Método | URL | Ação |
|---|---|---|
| GET | `/api/health/` | Verifica se a API está no ar |
| GET | `/api/produtos/` | Lista todos os produtos |
| POST | `/api/produtos/` | Cria um novo produto |
| GET | `/api/produtos/{id}/` | Detalhe de um produto |
| PUT | `/api/produtos/{id}/` | Atualiza um produto |
| DELETE | `/api/produtos/{id}/` | Remove um produto |

---

## Checklist Final

- [ ] RDS criado com status **Disponível**
- [ ] Endpoint do RDS anotado
- [ ] `app.zip` gerado com `manage.py` na raiz
- [ ] Ambiente EB criado com plataforma **Python**
- [ ] Upload do `app.zip` realizado
- [ ] 6 variáveis de ambiente configuradas no EB
- [ ] Status do ambiente EB: **Ok** (verde)
- [ ] `GET /api/health/` retorna `{"status": "ok"}`
- [ ] Conseguiu criar um produto via `POST /api/produtos/`
- [ ] Produto aparece na listagem via `GET /api/produtos/`

---

## Limpar os Recursos (ao final da aula)

> ⚠️ Para evitar cobranças, sempre encerre os recursos após o lab!

1. **Elastic Beanstalk:** Ações → **Encerrar ambiente**
2. **RDS:** Selecione o banco → **Ações** → **Excluir** (desmarque snapshot final para excluir mais rápido)

---

*Roteiro preparado para turma de Introdução ao Cloud Computing — IBMEC 2026.1*
