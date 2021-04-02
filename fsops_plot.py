"""
Script that plots benchmark data-visualizations.
"""
import gzip
import urllib.request
from plotnine.themes.theme_gray import theme_gray
from plotnine.themes.theme import theme
from plotnine.themes.elements import (element_line, element_rect,
                                      element_text, element_blank)
import sys
import pandas as pd
import numpy as np
import plotnine as p9

from plotnine import *
from plotnine.data import *

import warnings

from io import BytesIO

# this is the width of a column in the latex template
LATEX_TEMPLATE_COLUMNWIDTH = 84.70798

# the unit of the latex template column width
LATEX_TEMPLATE_COLUMNWDITH_UNIT = 'mm'

# this is the width of the plot
PLOT_WIDTH = LATEX_TEMPLATE_COLUMNWIDTH

# this is the size unit
PLOT_SIZE_UNIT = LATEX_TEMPLATE_COLUMNWDITH_UNIT

# this is the ration of the plot
PLOT_ASPECT_RATIO = 16/6

# this is the plot height
PLOT_HEIGHT = PLOT_WIDTH/PLOT_ASPECT_RATIO

# What machine, max cores, sockets, revision
MACHINES = [
    {
        'name': 'cloudlab2x',
        'cores': 32,
    }
]

class theme_my538(theme_gray):
    def __init__(self, base_size=6, base_family='DejaVu Sans'):
        theme_gray.__init__(self, base_size, base_family)
        bgcolor = '#FFFFFF'
        self.add_theme(
            theme(
                strip_margin=0,
                strip_margin_x=0,
                strip_margin_y=0,
                legend_box_margin=0,
                legend_margin=0,
                axis_text=element_text(size=base_size),
                axis_ticks=element_blank(),
                title=element_text(color='#3C3C3C'),
                legend_background=element_rect(fill='None'),
                legend_key=element_rect(fill='#FFFFFF', colour=None),
                panel_background=element_rect(fill=bgcolor),
                panel_border=element_blank(),
                panel_grid_major=element_line(
                    color='#D5D5D5', linetype='solid', size=0.5),
                panel_grid_minor=element_blank(),
                panel_spacing=0.10,
                plot_background=element_rect(
                    fill=bgcolor, color=bgcolor, size=1),
                strip_background=element_rect(size=0)),
            inplace=True)

def throughput_vs_cores(machine, df_linux, df_bespin, write_ratios=[0, 10, 60, 100]):
    open_file=[1, 16]
    data_set = []
    if df_linux is not None and df_bespin is not None:
        df_linux['benchmark'] = df_linux.apply(lambda row: "{}".format(
            row.benchmark.split(",")[0]), axis=1)
        df_bespin['benchmark'] = df_bespin.apply(lambda row: "{}".format(
            row.benchmark.split(",")[0]), axis=1)
        df_linux['bench'] = 'Linux Tmpfs'
        df_bespin['bench'] = 'NrOS NrFS'

        for open_files in df_bespin.open_files.unique():
            for writeratio in df_linux.write_ratio.unique():
                benchmark = df_linux.loc[(df_linux['benchmark'] == "mix") & (df_linux['ncores'] <= machine['cores'])
                                        & (df_linux['write_ratio'] == writeratio) & (df_linux['open_files'] == open_files)]

                if len(benchmark) == 0 or writeratio not in write_ratios or open_files not in open_file:
                    continue

                benchmark = benchmark.groupby(['write_ratio', 'ncores', 'bench', 'open_files'], as_index=False).agg(
                    {'operations': 'sum', 'duration': 'max'})
                benchmark['tps'] = benchmark['operations'] / benchmark['duration']
                data_set.append(benchmark)

                benchmark_bespin = df_bespin.loc[(df_bespin['benchmark'] == "mix") & (df_bespin['ncores'] <= machine['cores'])
                    & (df_bespin['write_ratio'] == writeratio) & (df_bespin['open_files'] == open_files)]
                benchmark_bespin = benchmark_bespin.groupby(['write_ratio', 'ncores', 'bench', 'open_files'], as_index=False).agg(
                    {'operations': 'sum', 'duration': 'max'})

                benchmark_bespin['tps'] = benchmark_bespin['operations'] / benchmark_bespin['duration']
                data_set.append(benchmark_bespin)

            benchmarks = pd.concat(data_set)

        #print(benchmarks)
        xskip = int(machine['cores']/8)
        p = ggplot(data=benchmarks,
                    mapping=aes(x='ncores',
                                y='tps',
                                color='bench',
                                shape='bench')) + \
            theme_my538() + \
            coord_cartesian(ylim=(0, None), expand=False) + \
            labs(y="Throughput [Melems/s]") + \
            theme(legend_position='top', legend_title=element_blank()) + \
            scale_x_continuous(breaks=[1] + list(range(xskip, 513, xskip)), name='# Threads') + \
            scale_y_continuous(labels=lambda lst: ["{:,}".format(x / 1_000_000) for x in lst]) + \
            scale_color_brewer(type='qual', palette='Set2') + \
            geom_point() + \
            geom_line() + \
            facet_grid(["write_ratio", "open_files"], scales="free_y") + \
            guides(color=guide_legend(nrow=1))

        p.save("{}-throughput-vs-cores.png".format(machine['name']),
                dpi=300, width=2.1*PLOT_WIDTH, height=2.7*PLOT_HEIGHT, units=PLOT_SIZE_UNIT)
        p.save("{}-throughput-vs-cores.pdf".format(machine['name']),
                dpi=300, width=2.7*PLOT_WIDTH, height=2.7*PLOT_HEIGHT, units=PLOT_SIZE_UNIT)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(
            "Usage: <linux fsops csv> <bespin fsops csv>.")
        exit(0)

    warnings.filterwarnings('ignore')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.expand_frame_repr', True)

    df_linux = pd.read_csv(sys.argv[1])
    df_bespin = pd.read_csv(sys.argv[2])
    throughput_vs_cores(MACHINES[0], df_linux, df_bespin)
