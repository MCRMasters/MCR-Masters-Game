from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Yaku
from app.score_calculator.yaku_check.yaku_checker import BlockYakuChecker


class TwoTerminalChowsChecker(BlockYakuChecker):
    def __init__(self, blocks: list[Block]):
        super().__init__(Yaku.TwoTerminalChows, blocks)

    def validate_basic_conditions(self) -> bool:
        return len(self.blocks) == self.DOUBLE and self.is_all_sequence()

    def check_yaku(self) -> bool:
        return (
            self.validate_basic_conditions()
            and self.count_type() == self.SINGLE
            and abs(self.blocks[0].tile - self.blocks[1].tile) == self.TERMINAL_GAP
        )
