import pytest

from app.services.game_manager.models.action import Action
from app.services.game_manager.models.enums import RelativeSeat
from app.services.game_manager.models.manager import ActionManager
from app.services.game_manager.models.types import ActionType


@pytest.mark.parametrize(
    "initial_action, push_actions_queue, final_action",
    [
        (
            [
                Action(type=ActionType.CHII, seat_priority=RelativeSeat.SHIMO),
                Action(type=ActionType.PON, seat_priority=RelativeSeat.KAMI),
            ],
            [Action(type=ActionType.PON, seat_priority=RelativeSeat.KAMI)],
            Action(type=ActionType.PON, seat_priority=RelativeSeat.KAMI),
        ),
        (
            [
                Action(type=ActionType.CHII, seat_priority=RelativeSeat.SHIMO),
                Action(type=ActionType.PON, seat_priority=RelativeSeat.KAMI),
            ],
            [Action(type=ActionType.CHII, seat_priority=RelativeSeat.KAMI)],
            None,
        ),
    ],
)
def test_action_manager(initial_action, push_actions_queue, final_action):
    action_manager = ActionManager(initial_action)
    for action in push_actions_queue:
        action_manager.push_action(action=action)
    assert final_action == action_manager.final_action
