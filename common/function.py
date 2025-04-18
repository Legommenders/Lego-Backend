from typing import Optional


def argparse(arguments):
    arguments = arguments.split(' ')[2:]
    kwargs = {}

    key: Optional[str] = None
    for arg in arguments:
        if key is not None:
            kwargs[key] = arg
            key = None
        else:
            assert arg.startswith('--')
            key = arg[2:]

    for key, value in kwargs.items():  # type: str, str
        if value == 'null':
            kwargs[key] = None
        elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            kwargs[key] = int(value)
        elif value.lower() == 'true':
            kwargs[key] = True
        elif value.lower() == 'false':
            kwargs[key] = False
        else:
            try:
                kwargs[key] = float(value)
            except ValueError:
                pass
    return kwargs


if __name__ == '__main__':
    print(argparse("python trainer.py --data config/recbench/automotive.yaml --model config/model/dcn_id.yaml --batch_size 5000 --lr 0.001 --lm glove --fast_eval false"))
