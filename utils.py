import re
import base64
import quopri
import email
from mailbox import mbox
from pathlib import Path
from ListDataset import ListDataset


def get_text_content(part: email.message.Message):
    content = part._payload
    headers = dict(part._headers)
    if "charset" in headers["Content-Type"]:
        bits = headers["Content-Type"].split("charset=")
        if bits[1].startswith('"'):
            charset = bits[1].split('"')[1]
        else:
            charset = re.split("\s", bits[1])[0]
    if "Content-Transfer-Encoding" in headers:
        match headers["Content-Transfer-Encoding"]:
            case "quoted-printable":
                content = quopri.decodestring(content).decode(charset)
            case "base64":
                content = base64.b64decode(content).decode(charset)
            case "8bit":
                content = content.encode(charset, "surrogateescape").decode("utf-8")
            case _:
                print(headers)
    return content


def get_text_messages(box: mbox) -> list[email.message.Message]:
    messages = []
    for msg in box:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    messages.append(part)
        else:
            if msg.get_content_type() == "text/plain":
                messages.append(msg)
    return messages


def get_text_contents(box: mbox) -> list[str]:
    return [get_text_content(e) for e in get_text_messages(box)]


def get_content_dataset(box: mbox) -> ListDataset:
    return ListDataset(data=get_text_contents(box))


def get_entity_books(parent_dir: Path, sub_dirs: list[str]) -> dict[str, list[str]]:
    entity_books = {}
    for e in sub_dirs:
        entity_book = parent_dir / e / "EntityBook"
        if entity_book.exists():
            entity_books[e] = [
                x.strip() for x in entity_book.read_text().split("\n--") if x.strip()
            ]
        else:
            entity_books[e] = []
    return entity_books


def write_entity_books(entity_books: dict[str, list[str]], parent_dir: Path):
    for k, v in entity_books.items():
        entity_book_file = parent_dir / k / "EntityBook"
        with entity_book_file.open("w+") as f:
            f.write("\n--\n".join(v))
            f.write("\n--")


def str_to_type(str_: str) -> str | float | bool:
    if str_.isnumeric():
        if "." in str_:
            return float(str_)
        else:
            return int(str_)
    if str_.lower() == "false":
        return False
    if str_.lower() == "true":
        return True
    return str_


def arglist_to_kwarg_dict(args: list[str]) -> dict[str, str | float | bool]:
    arg_dict = {}
    if all(["=" in arg for arg in args]):
        for e in args:
            parameter, value = e.split("=")
            arg_dict[parameter] = str_to_type(value)
    elif len(args) % 2 == 0:
        for i, e in enumerate(args):
            if i % 2:
                continue
            parameter = e
            value = e[i + 1]
            arg_dict[parameter] = str_to_type(value)
    else:
        raise Exception(
            "Malformatted kwarg parameters. Provide list of 'param=value' or alternating param value pairs"
        )
    return arg_dict
