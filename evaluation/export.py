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

def get_top_rank_models_per_datasets(replicate=5, metrics=None, datasets=None, top_k=1):
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
            tune_from = config.model.config.item_config.tune_from or ''
            embed = config.embed.name or 'null'
            lm = config.lm
            model = f'{model}{tune_from}.{lm}.{embed}'
            results[dataset].append(dict(
                model=model,
                **evaluation.prettify_performance(metrics=metrics),
            ))

    return results
