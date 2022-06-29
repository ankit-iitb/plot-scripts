"""
Script that plots benchmark data-visualizations.
"""
from plotnine.themes.theme_gray import theme_gray
from plotnine.themes.theme import theme
from plotnine.themes.elements import (element_line, element_rect,
                                      element_text, element_blank)
import sys
import pandas as pd

from plotnine import *
from plotnine.data import *

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


def heatmap(df):
    p = ggplot(data=df,
               mapping=aes(x='inter',
                           y='intra',
                           fill='tput')) + \
        theme_my538(base_size=12) + \
        labs(y="#Interop Threads") + \
        labs(x="#Intraop Threads") + \
        theme(legend_position="right", legend_title=element_blank()) + \
        geom_tile() + \
        geom_text(aes(label='tput')) + \
        facet_grid('~batch')

    p.save('heatmap.png')


if __name__ == '__main__':
    df = pd.read_csv(sys.argv[1])
    heatmap(df)
    sys.exit(0)
