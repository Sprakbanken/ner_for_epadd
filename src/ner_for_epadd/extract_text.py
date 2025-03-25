import re
import base64
import quopri
import email
from mailbox import mbox
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


def get_text_content(message: email.message.Message) -> str:
    content = message._payload
    headers = dict(message._headers)
    if "Content-Type" in headers and "charset" in headers["Content-Type"]:
        bits = headers["Content-Type"].split("charset=")
        if bits[1].startswith('"'):
            charset = bits[1].split('"')[1]
        else:
            charset = re.split("\s", bits[1])[0]
    else:
        logger.debug("No charset in Content-Type header, interpreting as acsii")
        content = content.encode("ascii", "surrogateescape").decode("utf-8")

    if "Content-Transfer-Encoding" in headers:
        match headers["Content-Transfer-Encoding"]:
            case "quoted-printable":
                content = quopri.decodestring(content).decode(charset)
            case "base64":
                content = base64.b64decode(content).decode(charset)
            case "8bit":
                content = content.encode(charset, "surrogateescape").decode("utf-8")
            case _:
                logger.warning(
                    "Unknown Content-Transfer-Encoding %s",
                    headers["Content-Transfer-Encoding"],
                )
    return content


def get_text_messages(box: mbox) -> dict[str, email.message.Message]:
    """Extract text messages from mbox and return a dict of message-id: message object"""
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
    """Extract text content from mbox and return a dict of message-id: message_text"""
    return {k: get_text_content(msg) for k, msg in get_text_messages(box).items()}
