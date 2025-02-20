# utils.py
def tile_num_to_string(tile_num: int) -> str:
    # 예: 0~8 -> "1m"~"9m", 9~17 -> "1p"~"9p", 18~26 -> "1s"~"9s", 27~33 -> "1z"~"7z"
    if 0 <= tile_num < 9:
        return f"{tile_num+1}m"
    elif 9 <= tile_num < 18:
        return f"{tile_num-8}p"
    elif 18 <= tile_num < 27:
        return f"{tile_num-17}s"
    elif 27 <= tile_num < 34:
        return f"{tile_num-26}z"
    elif tile_num == 34:
        return "0f"
    return "Unknown"

def tile_name_to_num(tile_name: str) -> int:
    if len(tile_name) != 2:
        return -1
    try:
        num = int(tile_name[0]) - 1
    except ValueError:
        return -1
    suit = tile_name[1]
    if suit == 'm':
        return num
    elif suit == 'p':
        return num + 9
    elif suit == 's':
        return num + 18
    elif suit == 'z':
        return num + 27
    return -1

def is_number(tile: int) -> bool:
    return 0 <= tile < 27

def is_honor(tile: int) -> bool:
    return 27 <= tile < 34
