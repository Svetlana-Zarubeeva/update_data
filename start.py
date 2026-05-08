"""!
@brief Модуль для запуска скриптов.
Порядок импорта не менять, если нужно добавить, добавляем в конец
"""
import logging
import sys


from pipelines.pipelines.okved.okved_gold_pipeline import main as okved_gold_pipeline
from pipelines.pipelines.ofdata.ofdata_bronze_pipeline import main as ofdata_bronze_pipeline
from pipelines.pipelines.ofdata.ofdata_silver_pipeline import main as ofdata_silver_pipeline
from pipelines.pipelines.dadata.dadata_bronze_pipeline import main as dadata_bronze_pipeline
from pipelines.pipelines.dadata.dadata_silver_pipeline import main as dadata_silver_pipeline
from pipelines.pipelines.gold.gold_pipeline import main as gold_pipeline


## Название ключей только в snake_case
modules = {
    'okved_gold_pipeline': okved_gold_pipeline,
    'ofdata_bronze_pipeline': ofdata_bronze_pipeline,
    'ofdata_silver_pipeline': ofdata_silver_pipeline,
    'dadata_bronze_pipeline': dadata_bronze_pipeline,
    'dadata_silver_pipeline': dadata_silver_pipeline,
    'gold_pipeline': gold_pipeline,
}


def run_menu():
    i = 1
    for key in modules:
        print(f'{i} - {key}')
        i += 1

    number = int(input('Number: '))
    if number >= i:
        raise Exception(f'Number {number} not found')

    executable = list(modules.values())[number - 1]

    params = input('Params: ')
    args, kwargs = get_params(params.split(' '))

    executable(*args, **kwargs)


def run_console():
    args, kwargs = [], {}

    if sys.argv[1] in modules:
        logging.debug('Start `' + sys.argv[1] + '` module')
        if len(sys.argv) > 2:
            args, kwargs = get_params(sys.argv[2:])

        modules[sys.argv[1]](*args, **kwargs)
    else:
        raise Exception(f'Module {sys.argv[1]} not found')


def get_params(params):
    args = []
    kwargs = {}

    for item in params:
        if not item:
            continue

        if '=' in item:
            key, value = item.split('=')
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            kwargs[key] = value
        else:
            value = item
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            args.append(value)

    return args, kwargs


if __name__ == '__main__':
    # формат входных данных либо перечисление (последовательные параметры),
    # либо через `=` (именованные параметры).
    # Пример команд:
    # python3 start.py elasticsearch lu rep
    # python3 start.py inpi_api_parse dump=True

    try:
        if len(sys.argv) > 1:
            run_console()
        else:
            run_menu()
    finally:
        pass
