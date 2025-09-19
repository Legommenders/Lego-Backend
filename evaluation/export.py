from oba import Obj

from evaluation.models import Evaluation, Experiment

RANKING_MODELS = {
    'dnn': 'DNN',
    'pnn': 'PNN',
    'deepfm': 'DeepFM',
    'dcn': 'DCN',
    'dcnv2': 'DCNv2',
    'din': 'DIN',
    'autoint': 'AutoInt',
    'finalmlp': 'FinalMLP',
    'gdcn': 'GDCN',
    'masknet': 'MaskNet',
}

TEXT_RANKING_MODELS = {k + '_text': v + '-TEXT' for k, v in RANKING_MODELS.items()}

RANKING_MODELS.update(TEXT_RANKING_MODELS)

MATCHING_MODELS = {
    'naml': 'NAML',
    'nrms': 'NRMS',
    'lstur': 'LSTUR',
    'miner': 'MINER',
    'bert-naml': 'BERT-NAML',
    'bert-nrms': 'BERT-NRMS',
    'bert-lstur': 'BERT-LSTUR',
    'bert-miner': 'BERT-MINER',
    'llama1-naml': 'Llama1-NAML',
    'llama1-nrms': 'Llama1-NRMS',
    'llama1-lstur': 'Llama1-LSTUR',
    'llama1-miner': 'Llama1-MINER',
}

MODELS = {**RANKING_MODELS, **MATCHING_MODELS}

DATASETS = {
    'automotive': 'Automotive',
    'books': 'Books',
    'cds': 'CDs',
    'ebnerd': 'EB-NeRD',
    'goodreads': 'Goodreads',
    'hm': 'H&M',
    'lastfm': 'Last.fm',
    'microlens': 'MicroLens',
    'mind': 'MIND',
    'netflix': 'Netflix',
    'pens': 'PENS',
    'yelp': 'Yelp',
}

METRICS = {
    'gauc': 'GAUC',
    'mrr': 'MRR',
    'ndcg@1': 'nDCG@1',
    'ndcg@5': 'nDCG@5',
}


def get_total_running_hours():
    running_seconds = 0
    for experiment in Experiment.objects.all():
        running_seconds += experiment.data_final_time - experiment.data_prep_time
    return running_seconds / 3600


def get_top_rank_models_per_datasets(replicate=5, metrics=None, datasets=None, top_k=1, return_table=False):

    def get_pretty_table(results, metrics, top_k):
        table_lines = []
        readable_rank = ['SOTA', 'Runner-up']
        for i in range(1, top_k):
            readable_rank.append(f'Rank-{i + 1}')
        num_columns_per_rank = len(metrics) + 1
        current_line = ['Dataset']
        for i in range(top_k):
            current_line.append("\\multicolumn{%s}{c}{%s}" % (num_columns_per_rank, readable_rank[i]))
        table_lines.append(current_line)
        table_lines.append([''] + ['Model', *metrics] * top_k)

        for dataset in results:
            dataset_results = results[dataset]
            dataset = DATASETS.get(dataset, dataset)
            current_line = [dataset]
            for i in range(top_k):
                current_line.append(dataset_results[i]['model'])
                for metric in metrics:
                    mean, std = dataset_results[i][metric.upper()]
                    current_line.append(f'{mean * 100:.2f} $\pm$ {std * 100:.2f}')
            table_lines.append(current_line)

        for index, line in enumerate(table_lines):
            table_lines[index] = ' & '.join(line) + ' \\\\'
        return '\n'.join(table_lines)

    top_ranks = dict()
    metrics = metrics or METRICS
    datasets = datasets or DATASETS

    for evaluation in Evaluation.objects.all():
        experiments = Experiment.objects.filter(evaluation=evaluation, is_completed=True)
        if experiments.count() < replicate:
            continue

        config = Obj(evaluation.prettify_configuration())
        dataset = config.data.name.lower().replace('rb', '')

        if dataset not in datasets:
            continue

        if dataset not in top_ranks:
            top_ranks[dataset] = []

        score = evaluation.export_rank_performance(metrics=metrics)
        top_ranks[dataset].append((evaluation, score))

    results = dict()

    for dataset in top_ranks:
        top_ranks[dataset].sort(key=lambda x: x[1], reverse=True)
        top_ranks[dataset] = top_ranks[dataset][:top_k]
        results[dataset] = []

        for evaluation, _ in top_ranks[dataset]:
            config = Obj(evaluation.prettify_configuration())
            model = config.model.name.lower()
            if model in MODELS:
                model = MODELS[model]
            # tune_from = config.model.config.item_config.tune_from or ''
            # embed = config.embed.name or 'null'
            # lm = config.lm
            # model = f'{model}'
            results[dataset].append(dict(
                model=model,
                **evaluation.prettify_performance(metrics=metrics),
            ))

    if return_table:
        return get_pretty_table(results, metrics, top_k)

    return results
