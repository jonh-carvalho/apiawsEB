## Guia de Instalação Manual (Portable) - PostgreSQL no Windows

Este roteiro foca na instalação via binários (ZIP), ideal para manter o sistema limpo e entender o funcionamento do banco.

---

## 1. Download e Extração

1. **Download:** Acesse o site da [EnterpriseDB](https://www.enterprisedb.com/download-postgresql-binaries) e baixe a versão desejada para **Windows x86-64** (recomenda-se a 16 ou superior).
2. **Extração:** 
   - Crie uma pasta na raiz do seu disco (ex: `C:\postgresql`).
   - Mova o conteúdo do arquivo ZIP para dentro desta pasta.
   - O caminho final dos executáveis deve ser algo como `C:\postgresql\bin`.

---

## 2. Configuração do PATH (Variáveis de Ambiente)

Para que o Windows reconheça os comandos `initdb`, `pg_ctl` e `psql` de qualquer lugar, adicione a pasta `bin` ao sistema:

1. No menu iniciar, pesquise por **"Editar as variáveis de ambiente do sistema"** e abra-o.
2. Clique no botão **Variáveis de Ambiente...**.
3. Em **Variáveis do Sistema**, localize a variável **Path** e clique em **Editar**.
4. Clique em **Novo** e cole o caminho da pasta `bin` (ex: `C:\postgresql\bin`).
5. Clique em **OK** em todas as janelas.

> **Nota:** Feche e abra novamente qualquer terminal (CMD ou PowerShell) que esteja aberto para que a mudança surta efeito.

---

## 3. Verificação Prévia

Antes de começar, certifique-se de que a pasta `bin` do PostgreSQL (onde você descompactou) está no seu **PATH** do sistema.
No terminal, digite:
```cmd
postgres --version
```
*Se o comando não for reconhecido, adicione o caminho completo da pasta `bin` às Variáveis de Ambiente do Windows.*

---

## 4. Inicializar o Cluster de Dados

1. Abra o terminal como **Administrador**.
2. Defina onde os dados serão salvos (ex: `C:\postgres_data`).
3. Execute o comando de inicialização:

```cmd
initdb -D "C:\postgres\data" -U postgres -A scram-sha-256 -W
```

**O que esses parâmetros fazem?**
* `-D`: Local da pasta de dados.
* `-U postgres`: Define o superusuário inicial.
* `-A scram-sha-256`: Define o método de autenticação mais seguro e moderno.
* `-W`: Força o prompt para você digitar a senha do usuário `postgres` agora mesmo.

---

## 5. Configurar a Variável PGDATA (Produtividade)

Para evitar ter que digitar `-D "C:\postgres_data"` em todos os comandos futuros, adicione uma variável de ambiente no Windows:
* **Nome:** `PGDATA`
* **Valor:** `C:\postgres\data`

---

## 6. Registrar como Serviço do Windows

Registre o banco para iniciar automaticamente com o Windows:

```cmd
pg_ctl register -N "PostgreSQL"
net start PostgreSQL
```

*Dica: Para verificar o status, use `pg_ctl status`.*

---

## 4. Acesso Inicial e Teste

Acesse o console interativo:
```cmd
psql -U postgres
```

No console do Postgres (`postgres=#`), você pode criar seu primeiro banco para o projeto Django:
```sql
CREATE DATABASE produtos_db;
\q
```

---

## Dicas de "Sobrevivência" e Solução de Problemas

* **Conflito de Porta:** Se o serviço não subir, verifique se a porta **5432** já está em uso (comum se você já instalou o Postgres via instalador .exe antes): `netstat -ano | findstr :5432`.
* **Acesso Externo:** Por padrão, o Postgres só aceita conexões do `localhost`. Se for usar o banco em rede ou via Docker, altere `listen_addresses = '*'` no arquivo `postgresql.conf`.
* **DBeaver/pgAdmin:** Para conectar via ferramentas visuais, use Host: `localhost`, Porta: `5432`, Usuário: `postgres` e a senha definida no Passo 1.
