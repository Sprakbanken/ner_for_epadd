import re
import base64
import quopri
import email
from mailbox import mbox
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


def get_text_content(part: email.message.Message) -> str:
    content = part._payload
    headers = dict(part._headers)
    if "Content-Type" in headers and "charset" in headers["Content-Type"]:
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


def get_text_messages(box: mbox) -> dict[str, email.message.Message]:
    # TODO: This only works is there is no more than 1 text/plain part per message-id...
    messages = {}
    for msg in box:
        if "message-id" in msg:
            msg_id = msg["message-id"].strip()
        else:
            msg_id = str(uuid4())
            logger.warning(
                "No message-id in message %s, creating a random one: %s",
                str(msg)[:50],
                msg_id,
            )
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    messages[msg_id] = part
        else:
            if msg.get_content_type() == "text/plain":
                messages[msg_id] = msg
    return messages


def get_text_contents(box: mbox) -> dict[str, str]:
    return {k: get_text_content(msg) for k, msg in get_text_messages(box).items()}


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
