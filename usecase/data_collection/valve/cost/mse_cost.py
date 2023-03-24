import numpy as np


def mse_cost(pred, target):
    assert len(pred.shape)   == 3
    assert len(target.shape) == 3

    assert   pred.shape[-1] == 1
    assert target.shape[-1] == 1

    mse = ((target - pred)**2).sum(axis=1).squeeze(-1)

    return mse