"""
Management command: seed_produtos
==================================
Popula o banco com um conjunto diversificado de produtos para demonstrar
as capacidades de armazenamento e consulta JSONB do PostgreSQL.

Uso:
    python manage.py seed_produtos            # insere os produtos (idempotente)
    python manage.py seed_produtos --limpar   # apaga todos os produtos antes de inserir
"""

from django.core.management.base import BaseCommand
from api.models import Produto


PRODUTOS = [
    # ------------------------------------------------------------------ #
    # Eletrônicos — atributos técnicos ricos, tags com metadados          #
    # ------------------------------------------------------------------ #
    {
        "nome": "Notebook Dell XPS 15",
        "descricao": "Notebook premium com tela OLED 4K e placa dedicada",
        "preco": "8999.90",
        "estoque": 12,
        "atributos": {
            "cor": "prata",
            "processador": "Intel Core i7-13700H",
            "ram_gb": 32,
            "ssd_gb": 1024,
            "tela_polegadas": 15.6,
            "resolucao": "3840x2400",
            "gpu": "NVIDIA RTX 4060",
            "voltagem": "bivolt",
            "garantia_anos": 2,
            "peso_kg": 1.86,
            "dimensoes": {"largura_cm": 34.4, "altura_cm": 1.86, "profundidade_cm": 23.5},
        },
        "tags": [
            {"nome": "notebook",      "prioridade": 1},
            {"nome": "eletrônico",    "prioridade": 1},
            {"nome": "premium",       "prioridade": 2},
            {"nome": "lançamento",    "prioridade": 3},
        ],
    },
    {
        "nome": "Notebook Lenovo IdeaPad 3",
        "descricao": "Notebook custo-benefício para uso cotidiano",
        "preco": "2799.90",
        "estoque": 30,
        "atributos": {
            "cor": "azul",
            "processador": "AMD Ryzen 5 5500U",
            "ram_gb": 8,
            "ssd_gb": 256,
            "tela_polegadas": 15.6,
            "resolucao": "1920x1080",
            "gpu": "AMD Radeon integrada",
            "voltagem": "bivolt",
            "garantia_anos": 1,
            "peso_kg": 1.65,
            "dimensoes": {"largura_cm": 36.2, "altura_cm": 1.99, "profundidade_cm": 25.2},
        },
        "tags": [
            {"nome": "notebook",      "prioridade": 1},
            {"nome": "eletrônico",    "prioridade": 1},
            {"nome": "custo-benefício", "prioridade": 2},
            {"nome": "promoção",      "prioridade": 2},
        ],
    },
    {
        "nome": "Smartphone Samsung Galaxy S25",
        "descricao": "Flagship Android com câmera de 200MP e 5G",
        "preco": "4299.90",
        "estoque": 50,
        "atributos": {
            "cor": "grafite",
            "processador": "Snapdragon 8 Gen 4",
            "ram_gb": 12,
            "armazenamento_gb": 256,
            "tela_polegadas": 6.2,
            "resolucao": "2340x1080",
            "camera_mp": 200,
            "bateria_mah": 4000,
            "5g": True,
            "voltagem": "bivolt",
            "garantia_anos": 1,
        },
        "tags": [
            {"nome": "smartphone",   "prioridade": 1},
            {"nome": "eletrônico",   "prioridade": 1},
            {"nome": "5g",           "prioridade": 2},
            {"nome": "lançamento",   "prioridade": 2},
        ],
    },
    {
        "nome": "Smartphone Motorola Moto G54",
        "descricao": "Smartphone intermediário com bateria de longa duração",
        "preco": "1099.90",
        "estoque": 80,
        "atributos": {
            "cor": "azul",
            "processador": "MediaTek Dimensity 7020",
            "ram_gb": 8,
            "armazenamento_gb": 256,
            "tela_polegadas": 6.5,
            "resolucao": "2400x1080",
            "camera_mp": 50,
            "bateria_mah": 6000,
            "5g": True,
            "voltagem": "bivolt",
            "garantia_anos": 1,
        },
        "tags": [
            {"nome": "smartphone",   "prioridade": 1},
            {"nome": "eletrônico",   "prioridade": 1},
            {"nome": "5g",           "prioridade": 2},
            {"nome": "promoção",     "prioridade": 2},
            {"nome": "custo-benefício", "prioridade": 3},
        ],
    },
    {
        "nome": "Smart TV LG OLED 55\"",
        "descricao": "TV OLED 4K com sistema webOS e Dolby Vision",
        "preco": "5499.90",
        "estoque": 8,
        "atributos": {
            "cor": "preto",
            "tecnologia": "OLED",
            "tela_polegadas": 55,
            "resolucao": "3840x2160",
            "hdr": ["Dolby Vision", "HDR10", "HLG"],
            "smart_tv": True,
            "sistema": "webOS 23",
            "voltagem": "bivolt",
            "garantia_anos": 2,
            "peso_kg": 16.5,
        },
        "tags": [
            {"nome": "tv",           "prioridade": 1},
            {"nome": "eletrônico",   "prioridade": 1},
            {"nome": "oled",         "prioridade": 2},
            {"nome": "premium",      "prioridade": 2},
        ],
    },
    {
        "nome": "Smart TV Samsung 50\" Crystal UHD",
        "descricao": "TV 4K com PurColor e processador Crystal 4K",
        "preco": "2299.90",
        "estoque": 15,
        "atributos": {
            "cor": "preto",
            "tecnologia": "LED",
            "tela_polegadas": 50,
            "resolucao": "3840x2160",
            "hdr": ["HDR10+"],
            "smart_tv": True,
            "sistema": "Tizen",
            "voltagem": "bivolt",
            "garantia_anos": 1,
            "peso_kg": 12.8,
        },
        "tags": [
            {"nome": "tv",           "prioridade": 1},
            {"nome": "eletrônico",   "prioridade": 1},
            {"nome": "4k",           "prioridade": 2},
            {"nome": "promoção",     "prioridade": 2},
        ],
    },
    # ------------------------------------------------------------------ #
    # Eletrodomésticos — atributos de instalação e eficiência             #
    # ------------------------------------------------------------------ #
    {
        "nome": "Geladeira Brastemp Frost Free 375L",
        "descricao": "Geladeira duplex com tecnamento Frost Free e painel eletrônico",
        "preco": "3199.90",
        "estoque": 10,
        "atributos": {
            "cor": "inox",
            "capacidade_litros": 375,
            "tipo": "duplex",
            "frost_free": True,
            "voltagem": "220V",
            "classificacao_energetica": "A",
            "garantia_anos": 2,
            "peso_kg": 68,
            "dimensoes": {"largura_cm": 60, "altura_cm": 173, "profundidade_cm": 67},
        },
        "tags": [
            {"nome": "eletrodoméstico", "prioridade": 1},
            {"nome": "geladeira",       "prioridade": 1},
            {"nome": "inox",            "prioridade": 2},
        ],
    },
    {
        "nome": "Máquina de Lavar Consul 11kg",
        "descricao": "Lavadora com função turbo economia e 12 programas",
        "preco": "1799.90",
        "estoque": 20,
        "atributos": {
            "cor": "branco",
            "capacidade_kg": 11,
            "tipo": "tanque_unico",
            "voltagem": "220V",
            "classificacao_energetica": "A",
            "garantia_anos": 2,
            "programas": 12,
            "peso_kg": 42,
        },
        "tags": [
            {"nome": "eletrodoméstico", "prioridade": 1},
            {"nome": "lavadora",        "prioridade": 1},
            {"nome": "promoção",        "prioridade": 2},
        ],
    },
    {
        "nome": "Ar Condicionado Split Inverter Midea 12.000 BTU",
        "descricao": "Ar condicionado com tecnologia Inverter e Wi-Fi",
        "preco": "2199.90",
        "estoque": 18,
        "atributos": {
            "cor": "branco",
            "capacidade_btu": 12000,
            "tipo": "split",
            "inverter": True,
            "wifi": True,
            "voltagem": "220V",
            "classificacao_energetica": "A+++",
            "garantia_anos": 1,
        },
        "tags": [
            {"nome": "eletrodoméstico", "prioridade": 1},
            {"nome": "ar-condicionado", "prioridade": 1},
            {"nome": "inverter",        "prioridade": 2},
            {"nome": "lançamento",      "prioridade": 2},
        ],
    },
    # ------------------------------------------------------------------ #
    # Periféricos — atributos de conectividade                            #
    # ------------------------------------------------------------------ #
    {
        "nome": "Monitor LG UltraWide 29\"",
        "descricao": "Monitor ultrawide IPS 2560x1080 com FreeSync",
        "preco": "1599.90",
        "estoque": 22,
        "atributos": {
            "cor": "preto",
            "tela_polegadas": 29,
            "resolucao": "2560x1080",
            "painel": "IPS",
            "taxa_hz": 75,
            "tempo_resposta_ms": 5,
            "freesync": True,
            "entradas": ["HDMI", "DisplayPort"],
            "voltagem": "bivolt",
            "garantia_anos": 2,
        },
        "tags": [
            {"nome": "monitor",      "prioridade": 1},
            {"nome": "periférico",   "prioridade": 1},
            {"nome": "ultrawide",    "prioridade": 2},
        ],
    },
    {
        "nome": "Teclado Mecânico Redragon Kumara",
        "descricao": "Teclado mecânico gamer com switch Red e retroiluminação RGB",
        "preco": "349.90",
        "estoque": 60,
        "atributos": {
            "cor": "preto",
            "layout": "ABNT2",
            "switch": "Red",
            "rgb": True,
            "conexao": "USB",
            "n_key_rollover": True,
            "garantia_anos": 1,
        },
        "tags": [
            {"nome": "periférico",  "prioridade": 1},
            {"nome": "teclado",     "prioridade": 1},
            {"nome": "gamer",       "prioridade": 2},
            {"nome": "rgb",         "prioridade": 3},
        ],
    },
    {
        "nome": "Mouse Logitech MX Master 3",
        "descricao": "Mouse sem fio ergonômico com scroll eletromagnético",
        "preco": "599.90",
        "estoque": 35,
        "atributos": {
            "cor": "grafite",
            "dpi_max": 8000,
            "botoes": 7,
            "conexao": ["USB-C", "Bluetooth"],
            "bateria_horas": 70,
            "garantia_anos": 2,
        },
        "tags": [
            {"nome": "periférico",   "prioridade": 1},
            {"nome": "mouse",        "prioridade": 1},
            {"nome": "sem-fio",      "prioridade": 2},
            {"nome": "premium",      "prioridade": 2},
        ],
    },
]


class Command(BaseCommand):
    help = "Popula o banco com produtos de amostra para demonstração de JSONB"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpar",
            action="store_true",
            help="Remove todos os produtos antes de inserir os novos",
        )

    def handle(self, *args, **options):
        if options["limpar"]:
            total = Produto.objects.count()
            Produto.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"  {total} produto(s) removido(s)."))

        criados = 0
        ignorados = 0
        for dados in PRODUTOS:
            _, novo = Produto.objects.get_or_create(
                nome=dados["nome"],
                defaults={k: v for k, v in dados.items() if k != "nome"},
            )
            if novo:
                criados += 1
            else:
                ignorados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed concluído: {criados} produto(s) criado(s), {ignorados} já existia(m)."
        ))
