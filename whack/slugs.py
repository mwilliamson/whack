def join(parts):
    for part in parts:
        if part is None:
            raise ValueError("part is None")
            
    return "_".join(part for part in parts)


def split(string):
    return string.split("_")
