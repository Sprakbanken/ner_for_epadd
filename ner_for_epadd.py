from argparse import ArgumentParser
from mailbox import mbox
from pathlib import Path
from transformers import pipeline
from utils import (
    arglist_to_kwarg_dict,
    get_entity_books,
    get_content_dataset,
    get_text_messages,
    write_entity_books,
)
from tqdm import tqdm
import errno
import os
import logging


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--mbox", type=Path, help="Path to .mbox file", required=True)
    parser.add_argument(
        "--entity_books",
        type=Path,
        help="Path to entity books directory (ex: /home/<username>/epadd-appraisal/user/data/sessions/EntityBooks)",
        required=True,
    )
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
    if not args.entity_books.exists():
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), str(args.entity_books)
        )

    pipe = pipeline(
        "token-classification",
        model=args.ner_model,
        aggregation_strategy="first",
    )

    labels = {e.split("-")[1] for e in pipe.model.config.label2id if "-" in e}

    category_directory_map = arglist_to_kwarg_dict(args.cat_dir_map)
    for e in labels:
        try:
            dirname = category_directory_map[e]
        except Exception as ex:
            logger.error(
                f"Model label {e} does not exist in category directoy map {category_directory_map}"
            )
            raise ex

        entity_book_dir = args.entity_books / dirname
        if not entity_book_dir.exists():
            logger.error(
                f"Category directory map maps model label {e} to {dirname}, but {entity_book_dir} does not exist."
            )
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), str(entity_book_dir)
            )

    box = mbox(
        args.mbox,
        create=False,
    )

    box = mbox(args.mbox, create=False)
    content_dataset = get_content_dataset(box)

    exception_indices = []
    logger.info("Run NER on mbox text content\n")
    try:
        res = [e for e in tqdm(pipe(content_dataset))]
    except Exception as ex:
        logger.warning(
            f"An exception happened while running the mbox contents through the NER model.\n{ex}\nWill run NER on each mbox message individually\n"
        )
        res = []
        for i, e in tqdm(enumerate(content_dataset), total=len(content_dataset)):
            try:
                pipe(e)
                res.append(e)
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

    entities = {
        (ent["word"], ent["entity_group"])
        for entlist in res
        for ent in entlist
        if ent["score"] >= args.threshold
    }

    logger.info(f"Found {len(entities)} unique entities in mbox")

    entity_books = get_entity_books(
        args.entity_books, sub_dirs=category_directory_map.values()
    )
    prev_lens = {category: len(book) for category, book in entity_books.items()}

    for name, ent_type in entities:
        entity_books[category_directory_map[ent_type]].append(name)

    for k, v in entity_books.items():
        entity_books[k] = sorted(list(set(v)))

    for category, book in entity_books.items():
        prev_len = prev_lens[category]
        current_len = len(book)
        logger.debug(
            f"Found {current_len - prev_len} new entities for category {category}"
        )

    write_entity_books(
        entity_books=entity_books,
        parent_dir=args.entity_books,
    )

    logger.info(f"Wrote all entities to {args.entity_books}")
