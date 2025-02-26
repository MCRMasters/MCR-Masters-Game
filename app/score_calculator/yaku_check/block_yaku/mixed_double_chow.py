from app.score_calculator.block.block import Block
from app.score_calculator.enums.enums import Yaku
from app.score_calculator.yaku_check.yaku_checker import BlockYakuChecker


class MixedDoubleChowChecker(BlockYakuChecker):
    def __init__(self, blocks: list[Block]):
        super().__init__(Yaku.MixedDoubleChow, blocks)

    def validate_basic_conditions(self) -> bool:
        return len(self.blocks) == self.DOUBLE and self.is_all_sequence()

    def check_yaku(self) -> bool:
        return (
            self.validate_basic_conditions()
            and self.count_type() == self.DOUBLE
            and self.blocks[0].tile.get_number() == self.blocks[1].tile.get_number()
        )
