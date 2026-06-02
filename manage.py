#!/usr/bin/env python
"""Utilitário de linha de comando do Django."""
import os
import sys

from dotenv import load_dotenv
load_dotenv()  # carrega o .env antes de qualquer configuração do Django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. "
            "Verifique se está instalado e o ambiente virtual ativado."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
