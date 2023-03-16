import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
from matplotlib import ticker, cm
import pathlib
from custom_service import join_with_mkdir


class TrajectoryVisualization:
    def __init__(self, dim, figsize=(5,5)):
        self.fig     = None
        self.ax      = None
        self.figsize = figsize
        self.dim     = dim


    def _initialize(self):
        self.fig, self.ax = plt.subplots(self.dim, 1, figsize=self.figsize)


    def plot_samples(self, samples):
        if self.fig is None: self._initialize()
        num_data, horizon, dim = samples.shape
        for d in range(dim):
            x = samples[:, :, d].transpose()
            self.ax[d].plot(x,
                linewidth  = 0.6,
                color      = "lightskyblue",
                # color      = "gray",
                alpha      = 0.35,
                marker     = 'o',
                markersize = 1.0,
                label      = "samples",
            )


    def plot_elites(self, elites):
        if self.fig is None: self._initialize()
        num_data, horizon, dim = elites.shape
        for d in range(dim):
            x = elites[:, :, d].transpose()
            self.ax[d].plot(x,
                linewidth  = 0.6,
                color      = "royalblue",
                alpha      = 0.5,
                marker     = 'o',
                markersize = 1.0,
                label      = "elites",
            )


    def plot_target(self, target):
        if self.fig is None: self._initialize()
        num_data, horizon, dim = target.shape
        for d in range(dim):
            x = target[:, :, d].transpose()
            self.ax[d].plot(x,
                linewidth  = 1.0,
                # color      = "darkmagenta",
                # color      = "black",
                color      = "orange",
                alpha      = 0.8,
                marker     = 'o',
                markersize = 1.5,
                label      = "target",
            )


    def _set_limit(self):
        for d in range(self.dim):
            self.ax[d].set_xlim()


    def save_plot(self, save_path):
        # plt.legend()
        # import ipdb; ipdb.set_trace()
        # self._set_limit()
        self.fig.savefig(join_with_mkdir(*(save_path,), is_end_file=True), dpi=300)


    def clear(self):
        if self.ax is None: return
        for d in range(self.dim):
            self.ax[d].cla()
