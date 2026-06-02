from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'produtos', views.ProdutoViewSet, basename='produto')

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('', include(router.urls)),

    # ------------------------------------------------------------------ #
    #  Endpoints de análise JSONB                                          #
    # ------------------------------------------------------------------ #
    path('analise/resumo/',         views.analise_resumo_geral,  name='analise-resumo'),
    path('analise/tags/',           views.analise_por_tag,        name='analise-tags'),
    path('analise/voltagem/',       views.analise_por_voltagem,   name='analise-voltagem'),
    path('analise/ram-notebooks/',  views.analise_ram_notebooks,  name='analise-ram'),
    path('analise/5g/',             views.analise_5g,             name='analise-5g'),
    path('analise/garantia/',       views.analise_garantia,       name='analise-garantia'),
]
