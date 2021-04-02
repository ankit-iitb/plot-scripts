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

from plotnine import *
from plotnine.data import *
import humanfriendly
from io import BytesIO
import gzip

import warnings

from plotnine.themes.elements import (element_line, element_rect,
                                      element_text, element_blank)
from plotnine.themes.theme import theme
from plotnine.themes.theme_gray import theme_gray

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
                strip_margin=0,
                strip_margin_x=1.6,
                strip_margin_y=1.6,
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


def plot_scalability(filename, machine, benchmark_name, df_linux,
                     df_bespin, df_barrelfish, df_barrelfish_vailla,
                     df_sv6):
    "Plots a throughput graph for various threads showing the throughput over time"

    print("\n" + bcolors.BOLD + ("+ Plotting '%s' on '%s'" %
                                 (benchmark_name, machine['name'])) + bcolors.RESET)

    dataframes = []

    if df_bespin is not None:
        df_bespin['os'] = "NrOS vMem"
        for name in df_bespin.benchmark.unique():
            MS_TO_SEC = 0.001
            # Bespin data format is different, it has a log entry for every second
            # We drop the first measurement and take the mean of the rest
            benchmark_bespin = df_bespin.loc[(df_bespin['benchmark'] == name) & (
                df_bespin['duration'] != 0) & (df_bespin['ncores'] <= machine['cores'])]

            # aggregate different runs based on `git_rev`:
            benchmark_bespin = benchmark_bespin.groupby(['ncores', 'benchmark', 'memsize', 'os', 'git_rev'], as_index=False).agg(
                {'operations': 'sum', 'thread_id': 'count', 'duration': 'max'})
            benchmark_bespin['tps'] = (
                benchmark_bespin['operations'] / ((benchmark_bespin['duration'] - 1000) * MS_TO_SEC)).fillna(0.0).astype(int)
            benchmark_bespin['tps_std'] = benchmark_bespin['tps']
            benchmark_bespin = benchmark_bespin.groupby(
                ['ncores', 'benchmark', 'memsize', 'os'], as_index=False).agg({'tps': 'mean', 'tps_std': 'std'})
            dataframes.append(benchmark_bespin)

    if df_linux is not None:
        df_linux['os'] = "Linux VMA"
        df_linux['benchmark'] = df_linux.apply(lambda row: "{}".format(
            row.benchmark.split("-")[0]), axis=1)
        for name in df_linux.benchmark.unique():
            benchmark = df_linux.loc[(df_linux['benchmark'] ==
                                      name) & (df_linux['ncores'] <= machine['cores'])]
            benchmark = benchmark.groupby(['ncores', 'benchmark', 'memsize', 'os'], as_index=False).agg(
                {'operations': 'sum', 'thread_id': 'count', 'duration': 'max'})
            MS_TO_SEC = 0.001
            benchmark['tps'] = (benchmark['operations'] /
                                (benchmark['duration'] * MS_TO_SEC)).fillna(0.0).astype(int)
            #print(benchmark)
            dataframes.append(benchmark)

    if df_barrelfish is not None:
        df_barrelfish['os'] = "Barrelfish Opt"
        df_barrelfish['benchmark'] = df_barrelfish.apply(lambda row: "{}".format(
            row.benchmark.split("-")[0]), axis=1)

        for name in df_barrelfish.benchmark.unique():
            benchmark_barrelfish = df_barrelfish.loc[df_barrelfish['benchmark'] == name]
            benchmark_barrelfish = benchmark_barrelfish.groupby(['ncores', 'benchmark', 'memsize', 'os'], as_index=False).agg(
                {'operations': 'sum', 'thread_id': 'count', 'duration': 'max'})
            MS_TO_SEC = 0.001
            benchmark_barrelfish['tps'] = (benchmark_barrelfish['operations'] /
                                           (benchmark_barrelfish['duration'] * MS_TO_SEC)).fillna(0.0).astype(int)
            # print(benchmark_barrelfish)
            dataframes.append(benchmark_barrelfish)

    if df_sv6 is not None:
        df_sv6 = df_sv6.rename(
            columns={"threads": "ncores", "throuhput": "tps"})
        df_sv6 = df_sv6.assign(tps=df_sv6['tps'] * 1000000)
        df_sv6['os'] = 'sv6'
        df_sv6['benchmark'] = 'maponly'
        dataframes.append(df_sv6)

    if df_barrelfish_vailla is not None:
        df_barrelfish_vailla['os'] = "Barrelfish Vanilla"
        df_barrelfish_vailla['benchmark'] = df_barrelfish_vailla.apply(lambda row: "{}".format(
            row.benchmark.split("-")[0]), axis=1)

        for name in df_barrelfish_vailla.benchmark.unique():
            benchmark_barrelfish_vanilla = df_barrelfish_vailla.loc[
                df_barrelfish_vailla['benchmark'] == name]
            benchmark_barrelfish_vanilla = benchmark_barrelfish_vanilla.groupby(['ncores', 'benchmark', 'memsize', 'os'], as_index=False).agg(
                {'operations': 'sum', 'thread_id': 'count', 'duration': 'max'})
            MS_TO_SEC = 0.001
            benchmark_barrelfish_vanilla['tps'] = (benchmark_barrelfish_vanilla['operations'] /
                                                   (benchmark_barrelfish_vanilla['duration'] * MS_TO_SEC)).fillna(0.0).astype(int)
            # print(benchmark_barrelfish)
            dataframes.append(benchmark_barrelfish_vanilla)

    benchmark = pd.concat(dataframes)
    benchmark['ncores'] = benchmark['ncores'].astype('int64', copy=False)
    xskip = int(machine['cores']/8)

    p = ggplot(data=benchmark, mapping=aes(x='ncores', y='tps', ymin=0, xmax=12, color='os', shape='os', group='os')) + \
        theme_my538() + \
        labs(y="Throughput [Mops/s]") + \
        theme(legend_position=(0.50, 0.95), legend_title=element_blank(), legend_direction='horizontal') + \
        scale_x_continuous(breaks=[1] + list(range(xskip, 513, xskip)), name='# Cores') + \
        scale_y_log10(labels=lambda lst: ["{:,.2f}".format(y / 1_000_000) for y in lst]) + \
        scale_color_manual(["#E78AC3", "#66C2A5", "#FC8D62", "#8DA0CB", "#A6D854", "#FFD92F", "#E5C494", "#B3B3B3"]) + \
        scale_shape_manual(values=[
            's',
            'o',
            '^',
            'D',
            'v',
            '*',
        ]) + \
        geom_point() + \
        geom_line() + \
        geom_errorbar(aes(ymin="tps-tps_std", ymax="tps+tps_std"), color='black') + \
        guides(color=guide_legend(nrow=1))

    print("\n" + bcolors.BOLD + ("+ Saving to '%s'" %
                                 ("{}-{}-throughput.png".format(filename, benchmark_name))) + bcolors.RESET)

    p.save("{}-{}-throughput.png".format(filename, benchmark_name),
           dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)
    p.save("{}-{}-throughput.pdf".format(filename, benchmark_name),
           dpi=300, width=PLOT_WIDTH, height=PLOT_HEIGHT, units=PLOT_SIZE_UNIT)

def parse_results(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return None

if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('display.expand_frame_repr', True)

    print('================================================================')
    print('VMOPS Throughput Plots')
    print('================================================================')

    if len(sys.argv) >= 3:
        print(
            "Usage: <linux vmops csv> <bespin vmops csv> [<barrelfish vmops csv>] [<sv6 vmops csv>].")
        df_linux = parse_results(sys.argv[1])
        df_bespin = parse_results(sys.argv[2])

        # If passes, then 3rd argument is for barrelfish.
        if len(sys.argv) > 3:
            df_barrelfish = parse_results(sys.argv[3])
        else:
            df_barrelfish = None
        
        # If passes, then 4th argument is for sv6.
        if len(sys.argv) > 4:
            df_sv6 = parse_results(sys.argv[4])
        else:
            df_sv6 = None
        filename, file_extension = os.path.splitext(sys.argv[1])
        machine=MACHINES[0]
        plot_scalability(machine['name'], machine, "maponly", df_linux,
                     df_bespin, df_barrelfish, None, df_sv6)