from django.tasks import task


@task
def somma(a, b):
    return a + b


@task(takes_context=True)
def fallisce(context):
    raise ValueError(f"tentativo numero {context.attempt}")
