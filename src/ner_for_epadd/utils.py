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
