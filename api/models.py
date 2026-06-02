from django.db import models


class Produto(models.Model):
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, default='')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    estoque = models.PositiveIntegerField(default=0)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)

    # ------------------------------------------------------------------ #
    #  Campos orientados a documento (JSONB no PostgreSQL)                 #
    #  atributos: especificações técnicas dinâmicas por categoria          #
    #  tags: lista de objetos {"nome": str, "prioridade": int}            #
    # ------------------------------------------------------------------ #
    atributos = models.JSONField(
        blank=True,
        default=dict,
        help_text='Especificações técnicas livres em formato chave-valor (JSONB).'
    )
    tags = models.JSONField(
        blank=True,
        default=list,
        help_text='Lista de palavras-chave para categorização e busca.'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return self.nome

