from .manifold_1d_transformer_numpy import Manifold1D_Transformer_Numpy
from .manifold_1d_transformer_torch import Manifold1D_Transformer_Torch
from .manifold_1d_value_object import TaskSpaceDifferentialPositionValue_1D_Manifold
from .manifold_1d_value_object import TaskSpacePositionValue_1D_Manifold


class Manifold_1D_Builder:
    def build(self, mode:str):
        if   mode == "numpy": Manifold1D_Transformer = Manifold1D_Transformer_Numpy()
        elif mode == "torch": Manifold1D_Transformer = Manifold1D_Transformer_Torch()
        else: raise NotImplementedError()

        return {
            "transformer"           : Manifold1D_Transformer,
            "TaskSpacePosition"     : TaskSpacePositionValue_1D_Manifold,
            "TaskSpaceDiffPosition" : TaskSpaceDifferentialPositionValue_1D_Manifold
        }
