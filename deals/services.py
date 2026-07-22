from .models import Pipeline, Stage

DEFAULT_STAGES = [
    ("Новый лид", False, False),
    ("Квалификация", False, False),
    ("Переговоры", False, False),
    ("Счёт выставлен", False, False),
    ("Оплачено", True, False),
    ("Отказ", False, True),
]


def create_default_pipeline(organization):
    pipeline = Pipeline.objects.create(organization=organization, name="Продажи")
    for order, (name, is_won, is_lost) in enumerate(DEFAULT_STAGES):
        Stage.objects.create(
            pipeline=pipeline, name=name, order=order, is_won=is_won, is_lost=is_lost
        )
    return pipeline
