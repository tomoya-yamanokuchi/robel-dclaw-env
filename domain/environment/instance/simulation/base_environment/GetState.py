import copy
import numpy as np
import sys; import pathlib; p = pathlib.Path(); sys.path.append(str(p.cwd()))
from domain.environment.kinematics.ForwardKinematics import ForwardKinematics
from custom_service import NTD
from domain.environment.task_space.manifold_1d.Manifold1D import Manifold1D


class GetState:
    def __init__(self, sim, State, task_space, EndEffectorValueObject):
        self.sim                    = sim
        self.State                  = State
        self.task_space             = task_space
        self.EndEffectorValueObject = EndEffectorValueObject
        self.forward_kinematics     = ForwardKinematics()


    def get_state(self):
        state                 = copy.deepcopy(self.sim.get_state())
        robot_position        = state.qpos[:9]
        end_effector_position = self.forward_kinematics.calc(robot_position).squeeze()
        task_space_position   = self.task_space.end2task(self.EndEffectorValueObject(NTD(end_effector_position))).value.squeeze()
        state = self.State(
            robot_position        = robot_position,
            object_position       = state.qpos[18:],
            robot_velocity        = state.qvel[:9],
            object_velocity       = state.qvel[18:],
            end_effector_position = end_effector_position,
            task_space_position   = task_space_position,
            time                  = state.time,
            act                   = state.act,
            udd_state             = state.udd_state,
        )
        return state
