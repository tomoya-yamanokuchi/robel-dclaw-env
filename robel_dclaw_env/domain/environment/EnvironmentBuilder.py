from typing import Dict, Union
from typing import TypedDict

from .instance.simulation.base_environment import AbstractEnvironment
from .task_space import AbstractTaskSpaceTransformer
from .EnvironmentFactory import EnvironmentFactory
from .task_space import TaskSpaceBuilder


class EnvDict(TypedDict):
    """Typed User definition."""
    env                   : AbstractEnvironment
    init_state            : str
    transformer           : AbstractTaskSpaceTransformer
    TaskSpacePosition     : str
    TaskSpaceDiffPosition : str


class EnvironmentBuilder():
    def build(self, config_env, mode="torch") -> EnvDict:
        env_sub, state_sub = EnvironmentFactory().create(env_name=config_env.env.env_name)
        env                = env_sub(config_env.env, use_render=False)
        init_state         = state_sub(**config_env.env.init_state)
        task_space         = TaskSpaceBuilder().build(config_env.env.env_name, mode)
        return {
            "env"                   : env,
            "init_state"            : init_state,
            "transformer"           : task_space["transformer"],
            "TaskSpacePosition"     : task_space["TaskSpacePosition"],
            "TaskSpaceDiffPosition" : task_space["TaskSpaceDiffPosition"],
        }


