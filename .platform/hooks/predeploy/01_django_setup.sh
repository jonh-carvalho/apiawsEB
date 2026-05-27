#!/bin/bash
# Ativa o ambiente virtual do Elastic Beanstalk
source /var/app/venv/*/bin/activate

# Garante que os comandos Django rodam no diretório correto do app
cd /var/app/staging

echo "=== Coletando arquivos estáticos ==="
python manage.py collectstatic --noinput

echo "=== Aplicando migrações do banco ==="
if python manage.py migrate --noinput; then
    echo "=== Migrações aplicadas com sucesso ==="
else
    echo "=== AVISO: migrate falhou — verifique o Security Group do RDS e as variáveis de ambiente ==="
    echo "=== O app será iniciado mesmo assim; corrija o banco e faça redeploy ==="
fi
