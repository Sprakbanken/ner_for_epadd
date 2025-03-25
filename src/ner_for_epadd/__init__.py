import argparse
from mailbox import mbox
from pathlib import Path
from transformers import pipeline
from ner_for_epadd.EmailDataset import EmailDataset
from src.ner_for_epadd.extract_text import (
    get_text_contents,
    get_text_messages,
)
from tqdm import tqdm
import logging
import json

logger = logging.getLogger(__name__)


def setup_logger(debug: bool) -> logging.Logger:
    log_level = logging.DEBUG if debug else logging.INFO
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logfile = log_dir / f"ner_for_epadd_{len(list(log_dir.iterdir()))}.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(logfile), logging.StreamHandler()],
    )


def run_NER_on_dataset(
    email_dataset: EmailDataset, NER_pipe: pipeline, debug: bool, box: mbox
) -> dict[str, list[dict]]:
    """Run NER on emails in email_dataset using NER_pipe"""
    exception_ids = []
    logger.info("Run NER on mbox text content")

    try:
        ner_entities = {
            message_id: entity_list
            for message_id, entity_list in zip(
                email_dataset.message_ids,
                tqdm(NER_pipe(email_dataset), desc="Running NER on email dataset"),
            )
        }
    except Exception as ex:
        logger.warning(
            f"An exception happened while running the mbox contents through the NER model.\n{ex}\nWill run NER on each mbox message individually\n"
        )
        ner_entities = {}
        for message_id, message_text in tqdm(
            zip(email_dataset.message_ids, email_dataset.message_texts),
            total=len(email_dataset),
            desc="Running NER on each message individually",
        ):
            try:
                ner_entities[message_id] = NER_pipe(message_text)
            except Exception as ex:
                logger.debug(
                    f"When running NER on message with message id {message_id} the following exception occured:\n{ex}"
                )
                exception_ids.append(message_id)

    if exception_ids:
        logger.info(f"Number of messages where NER failed: {len(exception_ids)}")

    if exception_ids and debug:
        logger.debug("Printing bad message headers:")
        messages = get_text_messages(box)
        bad_messages = [messages[i] for i in exception_ids]

        for msg in bad_messages:
            headers = dict(msg._headers)
            logger.debug(headers)
    return ner_entities


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mbox", type=Path, help="Path to .mbox file", required=True)
    parser.add_argument(
        "--ner_model",
        help="Model id on huggingface hub or path to local model",
        default="saattrupdan/nbailab-base-ner-scandi",
    )
    parser.add_argument(
        "--output", help="Path to output json file", type=Path, required=True
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
        help="If flagged, sets log level to debug (default is info)",
        action="store_true",
        default=False,
    )
    return parser.parse_args()


def main():
    args = get_args()

    setup_logger(args.debug)
    logger.info(args)

    box = mbox(
        args.mbox,
        create=False,
    )

    pipe = pipeline(
        "token-classification",
        model=args.ner_model,
        aggregation_strategy="first",
    )

    box = mbox(args.mbox, create=False)
    email_dict = get_text_contents(box)

    content_dataset = EmailDataset(data=email_dict)

    result = run_NER_on_dataset(content_dataset, pipe, box=box, debug=args.debug)

    filtered_result = []
    for message_id, entity_list in result.items():
        filtered_result.append(
            {
                "message-id": message_id,
                "entities": [
                    ent for ent in entity_list if ent["score"] >= args.threshold
                ],
            }
        )

    with open(args.output, "w") as outfile:
        json.dump(filtered_result, outfile, default=float, ensure_ascii=False, indent=2)
