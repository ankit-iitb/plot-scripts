#!/usr/bin/env python3

"""
Script that plots the vmops benchmark results.
"""
import sys
import os
import pandas as pd
import numpy as np
import plotnine as p9
import re
import urllib.request
import gzip

from plotnine import *
from plotnine.data import *
import humanfriendly

from io import BytesIO
import warnings

from plotnine.themes.elements import (element_line, element_rect,
                                      element_text, element_blank)
from plotnine.themes.theme import theme
from plotnine.themes.theme_gray import theme_gray

# this is the width of a column in the latex template
LATEX_TEMPLATE_COLUMNWIDTH = 84.70798

# the unit of the latex template column width
LATEX_TEMPLATE_COLUMNWDITH_UNIT = 'mm'

# this is the size unit
PLOT_SIZE_UNIT = LATEX_TEMPLATE_COLUMNWDITH_UNIT

# this is the ration of the plot
PLOT_ASPECT_RATIO = 16/6

# this is the width of the plot
PLOT_WIDTH = LATEX_TEMPLATE_COLUMNWIDTH * 2 / 3

# this is the plot height
PLOT_HEIGHT = PLOT_WIDTH/PLOT_ASPECT_RATIO

class bcolors:
    OK = '\033[32m'
    WARNING = '\033[33m'
    FAIL = '\033[1m\033[31m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

# What machine, max cores, linux vmops rev
MACHINES = [
    {
        'name': 'cloudlab2x',
        'cores': 32,
        'cores_timeseries': [1, 32],
        'cores_latency': [1, 8, 16, 24, 32],
    }
]

class theme_my538(theme_gray):
    def __init__(self, base_size=6, base_family='DejaVu Sans'):
        theme_gray.__init__(self, base_size, base_family)
        bgcolor = '#FFFFFF'
        self.add_theme(
            theme(
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
                panel_spacing=0.2,
                plot_background=element_rect(
                    fill=bgcolor, color=bgcolor, size=1),
                strip_background=element_rect(size=0)),
            inplace=True)


def plot_latency(filename, machine, benchmark_name, df_linux, df_bespin):
    "Plots a throughput graph for various threads showing the throughput over time"
    # csv format is:
    # git_rev,thread_id,benchmark,ncores,memsize,samples_total,sample_id,latency
    dataframes = []
    print("\n" + bcolors.BOLD + ("+ Plotting '%s' on '%s'" %
                                 (benchmark_name, machine['name'])) + bcolors.RESET)

    if df_bespin is not None:
        df_bespin['os'] = "Bespin"
        for name in df_bespin.benchmark.unique():
            benchmark_bespin = df_bespin.loc[df_bespin['benchmark'] == name]
            benchmark_bespin['os'] = 'NrOS VM'
            # Convert to ms
            benchmark_bespin['p100'] = benchmark_bespin['p100'] / (1000*1000)
            benchmark_bespin['p999'] = benchmark_bespin['p999'] / (1000*1000)
            benchmark_bespin['p99'] = benchmark_bespin['p99'] / (1000*1000)
            benchmark_bespin['p75'] = benchmark_bespin['p75'] / (1000*1000)
            benchmark_bespin['p50'] = benchmark_bespin['p50'] / (1000*1000)
            benchmark_bespin['p25'] = benchmark_bespin['p25'] / (1000*1000)
            benchmark_bespin['p1'] = benchmark_bespin['p1'] / (1000*1000)

            # print(benchmark_bespin)
            dataframes.append(benchmark_bespin)

    if df_linux is not None:
        df_linux['os'] = "Linux"
        benchmark_linux = df_linux.loc[df_linux['benchmark'] == benchmark_name]
        benchmark_linux['os'] = 'Linux'
        #print(benchmark_linux)
        dataframes.append(benchmark_linux)

    benchmark = pd.concat(dataframes)
    # print(benchmark)
    benchmark = benchmark[benchmark['ncores'].isin(machine['cores_latency'])]
    benchmark['ncores'] = benchmark['ncores'].astype('int64', copy=False)

    p = ggplot(data=benchmark, mapping=aes(x='factor(ncores)',
                                           ymax='p99',
                                           upper='p75',
                                           middle='p50',
                                           lower='p25',
                                           ymin='p1',
                                           color='os',
                                           fill='os')) + \
        theme_my538() + \
        scale_fill_brewer(type='qual', palette='Set2') + \
        theme(legend_position=(0.50, 0.95), legend_title=element_blank(), legend_direction='horizontal') + \
        labs(y="Latency [ms]") + \
        scale_x_discrete(name='# Cores') + \
        scale_y_log10(labels=lambda lst: ["{:,.2f}".format(x) for x in lst]) + \
        scale_color_brewer(type='qual', palette='Set2') + \
        geom_boxplot(stat='identity', notchwidth=0.53, alpha=0.2) + \
        guides(color=guide_legend(nrow=1))

    # geom_violin(mapping=None, data=None, stat='ydensity', position='dodge',
    #        na_rm=False, inherit_aes=True, show_legend=None, width=None,
    #        trim=True, scale='area', draw_quantiles=None, **kwargs)

    print("\n" + bcolors.BOLD + ("+ Saving to '%s'" %
                                 ("{}-{}-latency.png|pdf".format(filename, benchmark_name))) + bcolors.RESET)

    p.save("{}-{}-latency.png".format(filename, benchmark_name),
           dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)
    p.save("{}-{}-latency.pdf".format(filename, benchmark_name),
           dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)


def parse_results(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return None

if __name__ == '__main__':

    print('\n\n')
    print('================================================================')
    print('VMOPS Latency Plots')
    print('================================================================')

    warnings.filterwarnings('ignore')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.expand_frame_repr', True)

    if len(sys.argv) != 3:
        print(
            "Usage: <linux map-latency csv> <bespin map-latency csv>.")
    else:
        df_linux = parse_results(sys.argv[1])
        df_bespin = parse_results(sys.argv[2])
        machine = MACHINES[0]
        plot_latency(machine['name'] + "-vmops-latency", machine, "maponly", df_linux, df_bespin)
