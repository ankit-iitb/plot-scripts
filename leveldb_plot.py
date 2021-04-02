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
                panel_spacing=0.15,
                plot_background=element_rect(
                    fill=bgcolor, color=bgcolor, size=1),
                strip_background=element_rect(size=0)),
            inplace=True)

def throughput_vs_cores(df_linux, df_bespin):
    # Manual copy to reuse other plot scripts
    df_linux['cores'] = df_linux['ncores']
    df_linux['tps'] = df_linux['operations']
    df_linux['bench'] = 'Linux Tmpfs'

    df_bespin['cores'] = df_bespin['ncores']
    df_bespin['tps'] = df_bespin['operations']
    df_bespin['bench'] = 'NrOS NrFS'

    benchmarks = pd.concat([df_linux, df_bespin])

    #print(benchmarks)

    xskip = int(32/4)
    p = ggplot(data=benchmarks,
                mapping=aes(x='cores',
                            y='tps',
                            color='bench',
                            shape='bench')) + \
        theme_my538() + \
        coord_cartesian(ylim=(0, 1_300_000), xlim = (0.5, 32.5), expand=False) + \
        labs(y="Throughput [Kelems/s]") + \
        theme(legend_position=(0.50, 0.95), legend_title=element_blank(), legend_direction='horizontal') + \
        scale_x_continuous(breaks=[1] + list(range(xskip, 513, xskip)), name='# Threads') + \
        scale_y_continuous(labels=lambda lst: ["{:,}".format(x / 1_000) for x in lst]) + \
        scale_color_brewer(type='qual', palette='Set2') + \
        geom_point() + \
        geom_line() + \
        guides(color=guide_legend(nrow=1))

    p.save("leveldb.png", dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)
    p.save("leveldb.pdf", dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(
            "Usage: <linux leveldb csv> <bespin leveldb csv>.")
        exit(0)

    warnings.filterwarnings('ignore')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.expand_frame_repr', True)

    df_linux = pd.read_csv(sys.argv[1])
    df_bespin = pd.read_csv(sys.argv[2])
    throughput_vs_cores(df_linux, df_bespin)