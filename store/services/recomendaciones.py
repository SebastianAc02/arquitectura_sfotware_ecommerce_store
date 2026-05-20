from store.models import Product


def _etapa_de_vida(edad_anios: int) -> str:
    if edad_anios <= 1:
        return 'cachorro'
    if edad_anios <= 7:
        return 'adulto'
    return 'senior'


def recomendar_para_mascota(mascota, n: int = 4) -> list:
    """
    Retorna hasta N productos ordenados por relevancia para una mascota.

    Scoring:
      +3  etapa_vida del producto coincide con la del animal
      +2  peso del animal cae dentro del rango peso_min_kg / peso_max_kg
      +1  categoría Alimento (máxima prioridad nutricional)
      +1  tipo_mascota es exactamente el tipo del animal (vs 'todos')
    """
    tipo  = mascota.tipo
    etapa = _etapa_de_vida(mascota.edad)
    peso  = mascota.peso

    qs = (
        Product.objects
        .activos()
        .filter(tipo_mascota__in=[tipo, 'todos'])
        .select_related('category')
    )

    scored = []
    for p in qs:
        score = 0

        # Etapa de vida
        if p.etapa_vida in (etapa, 'todos', ''):
            score += 3

        # Rango de peso
        if p.peso_min_kg is not None and p.peso_max_kg is not None:
            if float(p.peso_min_kg) <= peso <= float(p.peso_max_kg):
                score += 2
        else:
            score += 1  # sin rango = aplica a todos, bonificación menor

        # Categoría alimento tiene mayor relevancia nutricional
        if p.category.slug == 'alimento':
            score += 1

        # Tipo exacto pesa más que 'todos'
        if p.tipo_mascota == tipo:
            score += 1

        scored.append((score, p.id, p))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [p for _, _, p in scored[:n]]
