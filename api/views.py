from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import Cast
from django.db.models import FloatField
from .models import Produto
from .serializers import ProdutoSerializer


@api_view(['GET'])
def health_check(request):
    """Endpoint de saúde — usado pelo EB para verificar se a app está no ar."""
    return Response({'status': 'ok', 'mensagem': 'API funcionando!'})


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Produtos.

    - GET    /api/produtos/        → lista todos
    - POST   /api/produtos/        → cria novo
    - GET    /api/produtos/{id}/   → detalhe
    - PUT    /api/produtos/{id}/   → atualiza
    - DELETE /api/produtos/{id}/   → remove
    """
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer


# ====================================================================== #
#  Endpoints de análise JSONB                                             #
#                                                                         #
#  Demonstram as consultas nativas ao campo JSONB do PostgreSQL           #
#  usando o ORM do Django sem escrever SQL manualmente.                   #
# ====================================================================== #

@api_view(['GET'])
def analise_por_tag(request):
    """
    GET /api/analise/tags/
    -----------------------------------------------------------------------
    Conta quantos produtos possuem cada tag (pelo campo "nome" dentro do
    array de objetos JSON).

    Técnica JSONB: filtra usando __contains sobre o array de objetos.
    Percorre todas as tags únicas encontradas nos produtos e conta
    quantos produtos as referenciam.

    Exemplo de resposta:
        [
            {"tag": "eletrônico",  "total": 6},
            {"tag": "promoção",    "total": 4},
            ...
        ]
    """
    # Coleta todos os nomes de tag distintos iterando sobre os produtos
    nomes_de_tags = set()
    for produto in Produto.objects.only('tags'):
        for item in (produto.tags or []):
            if isinstance(item, dict) and 'nome' in item:
                nomes_de_tags.add(item['nome'])
            elif isinstance(item, str):
                nomes_de_tags.add(item)

    resultado = []
    for tag in sorted(nomes_de_tags):
        # __contains filtra produtos cujo array tags contém o objeto {nome: tag}
        total = Produto.objects.filter(
            Q(tags__contains=[{'nome': tag}]) |    # array de objetos
            Q(tags__contains=[tag])                # array simples de strings
        ).count()
        resultado.append({'tag': tag, 'total': total})

    # Ordenar por total decrescente
    resultado.sort(key=lambda x: x['total'], reverse=True)
    return Response(resultado)


@api_view(['GET'])
def analise_por_voltagem(request):
    """
    GET /api/analise/voltagem/
    -----------------------------------------------------------------------
    Agrupa os produtos pelo valor do campo JSONB atributos->>'voltagem'.

    Técnica JSONB: __voltagem extrai o campo direto do objeto JSON.

    Exemplo de resposta:
        [
            {"voltagem": "bivolt", "total": 8, "preco_medio": "3427.39"},
            {"voltagem": "220V",   "total": 3, "preco_medio": "2399.90"},
            {"voltagem": null,     "total": 1, "preco_medio": "349.90"}
        ]
    """
    voltagens = {}
    for produto in Produto.objects.only('atributos', 'preco'):
        v = produto.atributos.get('voltagem') if produto.atributos else None
        chave = v or 'Não informado'
        if chave not in voltagens:
            voltagens[chave] = {'total': 0, 'soma': 0}
        voltagens[chave]['total'] += 1
        voltagens[chave]['soma'] += float(produto.preco)

    resultado = [
        {
            'voltagem': k,
            'total': v['total'],
            'preco_medio': f"{v['soma'] / v['total']:.2f}",
        }
        for k, v in sorted(voltagens.items(), key=lambda x: -x[1]['total'])
    ]
    return Response(resultado)


@api_view(['GET'])
def analise_ram_notebooks(request):
    """
    GET /api/analise/ram-notebooks/
    -----------------------------------------------------------------------
    Filtra apenas produtos com o atributo JSONB 'ram_gb' definido
    (notebooks e smartphones) e retorna estatísticas de RAM e preço.

    Técnica JSONB: __has_key verifica se a chave existe no objeto JSON;
    __ram_gb extrai o valor numérico para comparação.

    Exemplo de resposta:
        {
            "produtos_com_ram": 4,
            "ram_minima_gb": 8,
            "ram_maxima_gb": 32,
            "detalhes": [
                {"nome": "Notebook Dell XPS 15", "ram_gb": 32, "preco": "8999.90"},
                ...
            ]
        }
    """
    # __has_key: filtra produtos que têm a chave 'ram_gb' no JSONB
    qs = Produto.objects.filter(atributos__has_key='ram_gb').order_by('-preco')

    detalhes = [
        {
            'nome': p.nome,
            'ram_gb': p.atributos.get('ram_gb'),
            'processador': p.atributos.get('processador', '—'),
            'preco': str(p.preco),
        }
        for p in qs
    ]

    rams = [d['ram_gb'] for d in detalhes if d['ram_gb'] is not None]

    return Response({
        'produtos_com_ram': qs.count(),
        'ram_minima_gb': min(rams) if rams else None,
        'ram_maxima_gb': max(rams) if rams else None,
        'detalhes': detalhes,
    })


@api_view(['GET'])
def analise_5g(request):
    """
    GET /api/analise/5g/
    -----------------------------------------------------------------------
    Compara produtos com e sem suporte a 5G usando o campo booleano
    dentro do JSONB.

    Técnica JSONB: __5g=True filtra pelo valor booleano dentro do objeto.

    Exemplo de resposta:
        {
            "com_5g": {"total": 2, "preco_medio": "2699.90"},
            "sem_5g": {"total": 2, "preco_medio": "5499.90"},
            "produtos_5g": [...]
        }
    """
    com_5g = Produto.objects.filter(atributos__5g=True)
    sem_5g = Produto.objects.filter(atributos__has_key='5g', atributos__5g=False)

    def media_preco(qs):
        total = qs.count()
        if total == 0:
            return None
        soma = sum(float(p.preco) for p in qs)
        return f"{soma / total:.2f}"

    return Response({
        'com_5g': {
            'total': com_5g.count(),
            'preco_medio': media_preco(com_5g),
            'produtos': [
                {'nome': p.nome, 'preco': str(p.preco), 'ram_gb': p.atributos.get('ram_gb')}
                for p in com_5g.order_by('preco')
            ],
        },
        'sem_5g': {
            'total': sem_5g.count(),
            'preco_medio': media_preco(sem_5g),
            'produtos': [
                {'nome': p.nome, 'preco': str(p.preco)}
                for p in sem_5g.order_by('preco')
            ],
        },
    })


@api_view(['GET'])
def analise_garantia(request):
    """
    GET /api/analise/garantia/
    -----------------------------------------------------------------------
    Agrupa produtos por tempo de garantia e calcula preço médio por grupo.
    Demonstra filtros numéricos (__gte, __lte) sobre campos JSONB.

    Técnica JSONB: __garantia_anos__gte filtra pelo valor numérico
    dentro do objeto JSON, sem precisar de coluna separada.

    Exemplo de resposta:
        {
            "garantia_2_anos_ou_mais": {"total": 5, "preco_medio": "..."},
            "garantia_1_ano":          {"total": 6, "preco_medio": "..."},
            "sem_garantia_definida":   {"total": 1}
        }
    """
    dois_ou_mais = Produto.objects.filter(atributos__garantia_anos__gte=2)
    um_ano       = Produto.objects.filter(atributos__garantia_anos=1)
    sem_info     = Produto.objects.exclude(atributos__has_key='garantia_anos')

    def resumo(qs):
        total = qs.count()
        preco_medio = (
            f"{sum(float(p.preco) for p in qs) / total:.2f}" if total else None
        )
        return {
            'total': total,
            'preco_medio': preco_medio,
            'produtos': [{'nome': p.nome, 'preco': str(p.preco), 'garantia_anos': p.atributos.get('garantia_anos')} for p in qs],
        }

    return Response({
        'garantia_2_anos_ou_mais': resumo(dois_ou_mais),
        'garantia_1_ano':          resumo(um_ano),
        'sem_garantia_definida':   {'total': sem_info.count()},
    })


@api_view(['GET'])
def analise_resumo_geral(request):
    """
    GET /api/analise/resumo/
    -----------------------------------------------------------------------
    Painel consolidado com todas as análises JSONB em uma única chamada.
    Útil como visão geral do catálogo.
    """
    total = Produto.objects.count()
    if total == 0:
        return Response({'mensagem': 'Nenhum produto cadastrado. Execute: python manage.py seed_produtos'})

    precos = [float(p.preco) for p in Produto.objects.only('preco')]
    estoque_total = sum(p.estoque for p in Produto.objects.only('estoque'))

    # Contagem de produtos com 5G
    com_5g = Produto.objects.filter(atributos__5g=True).count()

    # Distribuição de voltagem
    dist_voltagem = {}
    for p in Produto.objects.only('atributos'):
        v = (p.atributos or {}).get('voltagem', 'Não informado')
        dist_voltagem[v] = dist_voltagem.get(v, 0) + 1

    # Garantia média
    garantias = [
        p.atributos.get('garantia_anos')
        for p in Produto.objects.only('atributos')
        if p.atributos and 'garantia_anos' in p.atributos
    ]
    media_garantia = f"{sum(garantias) / len(garantias):.1f}" if garantias else None

    return Response({
        'total_produtos': total,
        'estoque_total_unidades': estoque_total,
        'preco': {
            'minimo': f"{min(precos):.2f}",
            'maximo': f"{max(precos):.2f}",
            'medio':  f"{sum(precos) / len(precos):.2f}",
        },
        'produtos_com_5g': com_5g,
        'garantia_media_anos': media_garantia,
        'distribuicao_voltagem': dist_voltagem,
        'dica': 'Use /api/analise/tags/, /api/analise/voltagem/, /api/analise/ram-notebooks/, /api/analise/5g/ e /api/analise/garantia/ para análises detalhadas.',
    })

