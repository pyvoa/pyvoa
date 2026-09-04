
"""The matplotlib visualisation backend.

Static charts: the ``date``, ``versus`` and ``yearly`` plots, the three
histogram kinds, and maps. Every figure is created by the ``decomatplotlib``
decorator, which also stamps the pyvoa logo on it.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
import matplotlib.dates as mdates
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyvoa.kwargs_options import InputOption
from pyvoa.tools import (
    PyvoaError,
    min_max_range,
)


class visu_matplotlib:
    """MATPLOTLIB chart drawing methods ..."""

    def __init__(self,):
        """Pick the matplotlib backend that suits the environment.

        Chooses the inline backend inside a Jupyter kernel and TkAgg on a plain
        terminal or an IPython console, falling back to TkAgg if the detection
        itself fails. Doing this at construction keeps the choice out of the
        drawing methods.
        """
        import matplotlib
        self.av = InputOption()
        def set_matplotlib_backend():
            """Select the backend: inline under a Jupyter kernel, TkAgg otherwise."""
            try:
                from IPython import get_ipython
                ipy = get_ipython()
                if ipy is None:
                    # For classic terminal  (python)
                    matplotlib.use("TkAgg")
                elif "IPKernelApp" in ipy.config:
                    # For Jupyter notebook
                    matplotlib.use("module://matplotlib_inline.backend_inline")
                else:
                    # Cas IPython shell (ex : ipython en console)
                    matplotlib.use("TkAgg")
            except Exception:
                #in other case fallback vers TkAgg (fenêtre graphique)
                matplotlib.use("TkAgg")
        set_matplotlib_backend()

    def decomatplotlib(func):
        """Decorate creating the figure every matplotlib chart draws on.

        Builds a 10x5 figure and its axes, sets the title, and stamps the pyvoa
        logo faintly in the background. The figure, its axes and the pyplot
        module are passed on as the 'fig', 'ax' and 'plt' keyword arguments, so
        the drawing methods only have to draw.
        """
        def wrapper(self, **kwargs):
            """Build the figure, stamp the logo, then call the drawing method."""
            title = kwargs.get('title')
            im = mpimg.imread(kwargs['logo'])
            h, w = im.shape[:2]

            fig, ax = plt.subplots(1, 1, figsize=(10, 5))
            ax.set_title(title)
            #ax.grid(True)

            # Scale logo to ~15% of figure width
            logo_width = int(0.40 * fig.get_figwidth() * fig.dpi)
            logo_height = int(logo_width * h / w)  # Maintain aspect ratio

            fig_w, fig_h = fig.get_size_inches() * fig.dpi
            int(fig_w - logo_width - 20)    # 20px margin from right
            yo = int(fig_h - logo_height - 20)   # 20px margin from top

            # Resize the image to match calculated dimensions
            from PIL import Image
            pil_im = Image.fromarray((im * 255).astype('uint8'))
            im_resized = pil_im.resize((logo_width, logo_height))
            im_resized = np.array(im_resized) / 255.0

            fig.figimage(im_resized, xo=0, yo=0.5*yo, alpha=0.1)

            kwargs['fig'] = fig
            kwargs['ax'] = ax
            kwargs['plt'] = plt
            return func(self, **kwargs)
        return wrapper

    @decomatplotlib
    def matplotlib_date_plot(self,**kwargs):
        """Draw one or more variables against time.

        One line per location and per variable, the variables told apart by
        line style and the locations by colour. Location names are shortened
        for the legend, and the y axis honours the 'scale' option.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input', 'what', the
            'ax' supplied by decomatplotlib, and optionally 'scale' and
            'legend'.

        Returns
        -------
        The matplotlib axes the series were drawn on.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        ax = kwargs['ax']
        legend = kwargs.get('legend',None)
        kwargs['dicodisplayloc']
        ay_type = kwargs.get('scale',self.av.d_graphicsinput_args['scale'][0])

        ax.set_xlabel("date", fontsize=10)
        ax.set_ylabel(which, fontsize=10)
        ax.set_yscale(ay_type)
        ax.grid(True)
        st=['-','--',':']

        for idx, i in enumerate(which):
            df = pd.pivot_table(input, index='date', columns='where', values=i)
            for where in df.columns:
                if legend:
                    label = legend
                else:
                    label = f"{kwargs['dicodisplayloc'][where]}"
                if len(which)>1:
                    label =f"{kwargs['dicodisplayloc'][where]} — {i}"
                ax.plot(
                    df.index,
                    df[where],
                    label=label,
                    linestyle=st[idx]
                )
        ax.legend(loc="upper right", fontsize=8, title_fontsize=10,ncol=len(which))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
        return ax

    @decomatplotlib
    def matplotlib_versus_plot(self,**kwargs):
        """Plot one variable against another, rather than against time.

        Takes exactly two variables, the first on the x axis and the second on
        the y axis, one curve per location.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input', 'what' (two
            variables) and the 'ax' supplied by decomatplotlib.

        Returns
        -------
        The matplotlib axes the curves were drawn on.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        ax = kwargs['ax']
        loc = list(input['where'].unique())
        ax.set_xlabel(which[0], fontsize=10)
        ax.set_ylabel(which[1], fontsize=10)
        ax.grid(True)
        leg=[]
        for col in loc:
            pandy=input.loc[input['where']==col]
            ax.plot(pandy[which[0]], pandy[which[1]])
            leg.append(col)
        ax.legend(leg)
        return ax

    @decomatplotlib
    def matplotlib_yearly_plot(self,**kwargs):
        """Draw a yearly plot, one curve per calendar year.

        The number of locations displayed at once is capped by
        Max_Countries_Default.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        # title = kwargs.get('title')
        kwargs['plt']
        ax = kwargs['ax']
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)

        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        where = input['where'][0]

        d = input.allyears.unique()
        for i in d:
            df = pd.pivot_table(input.loc[input.allyears==i],index='dayofyear', columns='where', values=which)
            ax.plot(df.index,df,label=f'{i} {where}')
        month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        month_labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                        'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']

        ax.set_xticks(month_starts)
        ax.set_xticklabels(month_labels)
        ax.set_ylabel(which[0], fontsize=10)
        ax.grid(True)
        ax.legend()
        return ax

    @decomatplotlib
    def matplotlib_pie(self,**kwargs):
        """Draw a pie chart of one variable across locations.

        The number of locations displayed at once is capped by
        Max_Countries_Default.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        # plt = kwargs.get('plt')
        ax = kwargs.get('ax')

        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input['where'] = 'sum all location'
        input['where']= [kwargs['dicodisplayloc'][w] for w in input['where']]
        input = input.set_index('where')
        ax =  input.plot(kind="pie",y=which, autopct='%1.1f%%', legend=True,
        title=title, ylabel='', labeldistance=None,ax=ax)
        ax.legend(bbox_to_anchor=(1., 0.9), loc='upper left',title=which)
        ax.set_title(title)
        return ax


    @decomatplotlib
    def matplotlib_horizontal_histo(self,**kwargs):
        """Matplotlib horizon histo."""
        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        cmap = plt.get_cmap('Paired')
        ax = kwargs.get('ax')
        # fig = kwargs.get('fig')
        legend = kwargs.get('legend',None)

        input_sorted = input.sort_values(by=which,ascending=True)
        ax.set_title(title)
        ax.set_xlabel(which)
        ax.grid(True)
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input_sorted['where'] = 'sum all location'
        return ax.barh(input_sorted['where'], input_sorted[which],color=cmap.colors,label = legend)


    @decomatplotlib
    def matplotlib_histo(self, **kwargs):
        """Draw a histogram of one variable across locations.

        Bins the values between the smallest and the largest present, labelling
        the ticks in scientific notation so that the wide ranges epidemiological
        counts span stay readable.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input', 'which',
            optionally 'bins' (10 by default), and the 'ax' and 'plt'
            supplied by decomatplotlib.

        Returns
        -------
        The matplotlib axes the histogram was drawn on.
        """
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        input_df = kwargs.get('input').copy()
        bins = kwargs.get('bins', self.av.d_graphicsinput_args['bins'])
        which = kwargs.get('which')

        # -------------------------
        # bins
        # -------------------------
        min_val = input_df[which].min()
        max_val = input_df[which].max()

        if not bins:
            bins = 11

        edges = np.linspace(min_val, max_val, bins + 1)

        # assign bins
        input_df["bin"] = pd.cut(
            input_df[which],
            bins=edges,
            include_lowest=True
        )

        # pivot: bin x country
        pivot = (
            input_df
            .groupby(["bin", "where"], observed=False)
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        countries = pivot.columns
        colors = plt.cm.tab20(np.linspace(0, 1, len(countries)))

        # Position des barres
        x = np.arange(len(pivot))
        bottom = np.zeros(len(pivot))

        for i, country in enumerate(countries):
            ax.bar(
                x,
                pivot[country].values,
                bottom=bottom,
                label=country,
                color=colors[i],
                alpha=0.85
            )
            bottom += pivot[country].values

        # -------------------------
        # Centres des bins
        # -------------------------
        centers = (edges[:-1] + edges[1:]) / 2

        def format_sci(x):
            """Format a positive number as LaTeX scientific notation.

            Returns '' for anything not positive, since the labels are drawn on a
            log-friendly axis where such a value has no place.
            """
            if x <= 0:
                return ""

            exp = int(np.floor(np.log10(x)))
            mant = x / 10**exp
            mant = np.round(mant, 1)

            if mant == 1:
                return rf"$10^{{{exp}}}$"
            else:
                return rf"${mant:g}\times10^{{{exp}}}$"

        # Les positions des ticks correspondent aux positions des barres
        ax.set_xticks(x)
        ax.set_xticklabels([format_sci(c) for c in centers])

        ax.set_xlabel(which)
        ax.set_ylabel("frequency")

        ax.legend(
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0
        )

        ax.grid(True)

        return ax
    @decomatplotlib
    def matplotlib_map(self,**kwargs):
        """Matplotlib map display."""
        import contextily as cx
        import numpy as np
        from matplotlib.ticker import ScalarFormatter

        # plt.get_cmap, not plt.cm.get_cmap: the latter was removed in
        # matplotlib 3.9, which made every matplotlib map raise.
        cmap = plt.get_cmap("viridis").reversed()
        ax = kwargs.get('ax')
        ax.axis('off')

        input = kwargs.get('input')
        which = kwargs.get('which')
        title = kwargs.get('title')
        tile = kwargs.get('tile')
        typeofmap = kwargs.get('typeofmap')
        if typeofmap == 'dense':
            tile = None
        # The frames arrive labelled EPSG:4326 whatever their units: the world
        # geometries are in Web Mercator metres, the dense country geometries in
        # degrees. Both the minimum extent below and the CRS handed to contextily
        # depend on which one it is, so read it off the extent instead of
        # assuming metres — a 10 km floor is 10 000 degrees on a lon/lat frame,
        # which is what drew metropolitan France as a speck in a world-sized box.
        minx, miny, maxx, maxy = input.total_bounds
        in_degrees = abs(minx) <= 180 and abs(maxx) <= 180 and abs(miny) <= 90 and abs(maxy) <= 90
        data_crs = "EPSG:4326" if in_degrees else "EPSG:3857"
        minimum_extent = 1 if in_degrees else 10_000        # one degree, or 10 km

        dx = max(maxx - minx, minimum_extent)
        dy = max(maxy - miny, minimum_extent)

        factor = 0.5 if len(input) < 10 else 0.1

        minx -= dx * factor
        maxx += dx * factor
        miny -= dy * factor
        maxy += dy * factor
        ax.set_xlim(float(minx), float(maxx))
        ax.set_ylim(float(miny), float(maxy))
        ax.set_aspect('equal')

        #   fig = ax.get_figure()
        #fig.set_figwidth(16)
        #ratio = (maxy - miny) / (maxx - minx)
        #fig.set_figheight(fig.get_figwidth() * ratio)
        # color range
        min_col, max_col = min_max_range(np.nanmin(input[which]), np.nanmax(input[which]))
        # The units the frame is actually in, not Lambert-93: overriding every
        # frame to EPSG:2154 mislabelled both the world and the dense maps.
        input = input.set_crs(data_crs, allow_override=True)

        # plot
        input_missing = input[
            input['from_db'] == False
            ]
        input = input[
            input['from_db'] == True
            ]

        plot = input.plot(
            column=which,
            ax=ax,
            legend=True,
            cmap=cmap,
            vmin=min_col,
            vmax=max_col,
            edgecolor='black',
            linewidth=0.5,
            legend_kwds={
                'label': which,
                'orientation': "horizontal",
                'pad': 0.01,
                'shrink': 0.5
            }
        )
        plot = input_missing.plot(
            ax=ax,
            color='#FCE4EC',
            edgecolor='black',
        )
        cbar = plot.get_figure().axes[-1]
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((-2, 3))

        cbar.xaxis.set_major_formatter(formatter)
        cbar.tick_params(labelsize=8)

        ax.set_axis_off()
        ax.set_title(title)

        # basemap
        if tile is not None:
            if tile == 'openstreet':
                cx.add_basemap(
                ax,
                crs=data_crs,
                source=cx.providers.OpenStreetMap.Mapnik,
                headers={
                    "User-Agent": "pyvoa/<version> (+https://github.com/pyvoa/pyvoa)"
                },
                )
            elif tile == 'esri':
                cx.add_basemap(
                    ax,
                    crs=data_crs,
                    source=cx.providers.Esri.WorldStreetMap,
                )

            elif tile == 'stamen':
                cx.add_basemap(
                    ax,
                    crs=data_crs,
                    source=cx.providers.Stamen.TonerLite,
                )

            elif tile == 'positron':
                cx.add_basemap(
                    ax,
                    crs=data_crs,
                    source=cx.providers.CartoDB.PositronNoLabels,
                )

            else:
                raise PyvoaError("Don't know what kind of tile it is...")
        return ax
