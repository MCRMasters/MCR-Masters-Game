# interop.py
from hand import Hand, WinningCondition
from block import Block, BlockType, BlockSource

def get_hu_yaku_score_data(hand_data: dict, condition_data: dict) -> dict:
    """
    hand_data와 condition_data 딕셔너리를 받아 Hand 객체를 구성한 후,
    야쿠 점수를 계산하여 반환합니다.
    """
    hand = Hand()
    hand.closed_tiles = hand_data.get("ClosedTiles", [0] * 35)
    hand.opened_tiles = hand_data.get("OpenedTiles", [0] * 35)
    call_blocks = []
    for block_info in hand_data.get("CallBlocks", []):
        block = Block(BlockType(block_info["Type"]), block_info["Tile"],
                      BlockSource(block_info["Source"]), block_info["SourceTileIndex"])
        call_blocks.append(block)
    hand.call_blocks = call_blocks

    winning_condition = WinningCondition(
        tile=condition_data.get("WinningTile", -1),
        is_discarded=condition_data.get("IsDiscarded", False),
        is_last_tile_in_the_game=condition_data.get("IsLastTileInTheGame", False),
        is_last_tile_of_its_kind=condition_data.get("IsLastTileOfItsKind", False),
        is_replacement_tile=condition_data.get("IsReplacementTile", False),
        is_robbing_the_kong=condition_data.get("IsRobbingTheKong", False),
        seat_wind=condition_data.get("SeatWind", 0),
        round_wind=condition_data.get("RoundWind", 0)
    )

    total_tiles = sum(hand.closed_tiles) + len(call_blocks) * 3
    if total_tiles != 14:
        return {}

    hand.closed_tiles[winning_condition.tile] -= 1
    if hand.closed_tiles[winning_condition.tile] < 0:
        return {}

    hand.get_keishiki_tenpai_tiles()
    if not hand.keishiki_tenpai_tiles:
        return {}

    hand.closed_tiles[winning_condition.tile] += 1
    winning_condition.count_winning_conditions = len(hand.keishiki_tenpai_tiles)
    hand.divide_blocks(winning_condition)
    return hand.yaku_score_list

def get_tenpai_tile_score_data(hand_data: dict, condition_data: dict) -> dict:
    """
    텐파이 타일별 점수 데이터를 계산하여 {타일번호: {'tsumoScore': X, 'ronScore': Y}} 형식으로 반환합니다.
    """
    hand = Hand()
    hand.closed_tiles = hand_data.get("ClosedTiles", [0] * 35)
    hand.opened_tiles = hand_data.get("OpenedTiles", [0] * 35)
    call_blocks = []
    for block_info in hand_data.get("CallBlocks", []):
        block = Block(BlockType(block_info["Type"]), block_info["Tile"],
                      BlockSource(block_info["Source"]), block_info["SourceTileIndex"])
        call_blocks.append(block)
    hand.call_blocks = call_blocks

    winning_condition = WinningCondition(
        tile=condition_data.get("WinningTile", -1),
        is_discarded=condition_data.get("IsDiscarded", False),
        is_last_tile_in_the_game=condition_data.get("IsLastTileInTheGame", False),
        is_last_tile_of_its_kind=condition_data.get("IsLastTileOfItsKind", False),
        is_replacement_tile=condition_data.get("IsReplacementTile", False),
        is_robbing_the_kong=condition_data.get("IsRobbingTheKong", False),
        seat_wind=condition_data.get("SeatWind", 0),
        round_wind=condition_data.get("RoundWind", 0)
    )

    total_tiles = sum(hand.closed_tiles) + len(call_blocks) * 3
    if total_tiles != 13:
        return {}

    if hand.closed_tiles[winning_condition.tile] < 0:
        return {}

    hand.get_keishiki_tenpai_tiles()
    if not hand.keishiki_tenpai_tiles:
        return {}

    winning_condition.count_winning_conditions = len(hand.keishiki_tenpai_tiles)
    tile_scores = {}
    for tile in hand.keishiki_tenpai_tiles:
        hand.closed_tiles[tile] += 1
        winning_condition.tile = tile
        winning_condition.is_discarded = False
        hand.divide_blocks(winning_condition)
        tsumo_score = hand.highest_score
        winning_condition.is_discarded = True
        hand.divide_blocks(winning_condition)
        ron_score = hand.highest_score
        tile_scores[tile] = {"tsumoScore": tsumo_score, "ronScore": ron_score}
        hand.closed_tiles[tile] -= 1
    return tile_scores
