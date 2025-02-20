# main.py
from hand import Hand, WinningCondition
from utils import tile_num_to_string
from get_score_yaku import get_hu_yaku_score_data, get_tenpai_tile_score_data

def main():
    # 예시: 빈 손패 데이터 (실제 사용 시 적절한 타일 분포로 채워야 합니다)
    hand_data = {
        "ClosedTiles": [0] * 35,
        "OpenedTiles": [0] * 35,
        "CallBlocks": []
    }
    condition_data = {
        "WinningTile": 5,  # 예: 6m (인덱스 5)
        "IsDiscarded": False,
        "IsLastTileInTheGame": False,
        "IsLastTileOfItsKind": False,
        "IsReplacementTile": False,
        "IsRobbingTheKong": False,
        "RoundWind": 0,
        "SeatWind": 0
    }
    
    yaku_scores = get_hu_yaku_score_data(hand_data, condition_data)
    print("Yaku Scores:", yaku_scores)
    
    tenpai_scores = get_tenpai_tile_score_data(hand_data, condition_data)
    print("Tenpai Tile Scores:", tenpai_scores)

if __name__ == '__main__':
    main()
