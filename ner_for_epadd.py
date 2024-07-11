from argparse import ArgumentParser
from mailbox import mbox
from pathlib import Path
from transformers import pipeline
from DictDataset import DictDataset
from utils import (
    arglist_to_kwarg_dict,
    get_text_contents,
    get_text_messages
)
from tqdm import tqdm
import errno
import os
import logging
import json
import pprint


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--mbox", type=Path, help="Path to .mbox file", required=True)
    parser.add_argument(
        "--ner_model",
        help="Model id on huggingface hub or path to local model",
        default="saattrupdan/nbailab-base-ner-scandi",
    )
    parser.add_argument(
        "--cat_dir_map",
        nargs="+",
        help="Key value pairs that map ner model categories to entitybook directories.",
        default=["PER=Person", "LOC=Place", "ORG=Organisation", "MISC=Other"],
    )
    parser.add_argument(
        "--output",
        help="Path to output json file",
        type=Path,
        required=False
    )
    parser.add_argument(
        "--threshold",
        help="NER model threshold (predicted entities with scores lower than threshold are ignored)",
        default=0.8,
        type=float,
    )
    parser.add_argument(
        "--debug",
        "-d",
        help="Set log level to debug",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    logger = logging.getLogger()
    ch = logging.StreamHandler()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if not args.mbox.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(args.mbox))

    pipe = pipeline(
        "token-classification",
        model=args.ner_model,
        aggregation_strategy="first",
    )

    labels = {e.split("-")[1] for e in pipe.model.config.label2id if "-" in e}

    box = mbox(
        args.mbox,
        create=False,
    )

    box = mbox(args.mbox, create=False)
    msg_dict = get_text_contents(box)
    content_dataset = DictDataset(data=msg_dict)

    exception_indices = []
    logger.info("Run NER on mbox text content\n")

    try:
        res = {k:val for k, val in zip(content_dataset.keys, tqdm(pipe(content_dataset)))}
    except Exception as ex:
        logger.warning(
            f"An exception happened while running the mbox contents through the NER model.\n{ex}\nWill run NER on each mbox message individually\n"
        )
        res = {}
        for k, e in tqdm(zip(content_dataset.keys, content_dataset.values), total=len(content_dataset)):
            try:
                res[k] = pipe(e)
            except Exception as ex:
                logger.debug(
                    f"When running NER on message number {i} the following exception occured:\n{ex}"
                )
                exception_indices.append(i)

    if exception_indices:
        logger.info(f"Number of messages where NER failed: {len(exception_indices)}")

    if exception_indices and args.debug:
        logger.debug("Printing bad message headers:")
        messages = get_text_messages(box)
        bad_messages = [messages[i] for i in exception_indices]

        for msg in bad_messages:
            headers = dict(msg._headers)
            logger.debug(headers)

    filtered = {
        msg_id:[ent for ent in entities if ent["score"] >= args.threshold]
        for msg_id, entities in res.items()
    }

    write_to_file = False
    if args.output:
        if os.path.exists(args.output):
            answer = input(f"Output file {args.output} exists already, overwrite? [y/n]")
            write_to_file = answer.lower() == "y"
        else:
            write_to_file = True

    if write_to_file:
        with open(args.output, 'w') as outfile:
            json.dump(filtered, outfile, default=float, ensure_ascii=False,indent=2)
    else:
        pprint.pp(filtered, indent = 2)
