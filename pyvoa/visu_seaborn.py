
"""The seaborn visualisation backend.

Static statistical charts: the ``date``, ``versus`` and ``yearly`` plots and
the three histogram kinds. It has no map, which is why ``AllVisu`` refuses
``map()`` for this backend. Built on matplotlib, so the figures it returns are
matplotlib ones.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
from functools import wraps

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import seaborn as sns

from pyvoa.tools import PyvoaWarning


class visu_seaborn:
    ######SEABORN#########
    ######################
    """The seaborn backend, drawing static statistical charts.

    Offers the 'date', 'versus' and 'yearly' plots and the three histogram
    kinds; it has no map, which is why AllVisu refuses map() for this
    backend. Built on matplotlib, so the figures it returns are matplotlib
    ones.
    """

    def __init__(self,):
        """Pick the matplotlib backend that suits the environment.

        Chooses the inline backend inside a Jupyter kernel and TkAgg on a plain
        terminal or an IPython console, falling back to TkAgg if the detection
        itself fails.
        """
        import matplotlib
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

    def decoplotseaborn(func):
        """Decorate seaborn plot."""
        @wraps(func)
        def inner_plot(self, **kwargs):
            """Build the figure, stamp the logo and title, then call the plot method.

            Passes the pyplot and seaborn modules on as the 'plt' and 'sns' keyword
            arguments.
            """
            im = mpimg.imread(kwargs['logo'])
            _h, w = im.shape[:2]
            fig, _ax = plt.subplots(1, 1,figsize=(10, 5))
            fig_w, fig_h = fig.get_size_inches() * fig.dpi
            xo = int(0.25*(fig_w-w))
            yo = int(0.3 * fig_h)
            fig.figimage(im, xo=xo, yo=yo, alpha=.1)
            title = kwargs.get('title')
            plt.title(title)
            kwargs['plt'] = plt
            kwargs['sns'] = sns
            return func(self, **kwargs)
        return inner_plot

    def decohistseaborn(func):
        """Decorate seaborn histogram."""
        @wraps(func)
        def inner_hist(self,**kwargs):
            """Reduce the series to one row per location before drawing.

            Keeps each location's most recent value and sorts by decreasing value,
            so the histogram shows a ranking rather than a time series.
            """
            input = kwargs.get('input')
            which = kwargs.get('which')
            if isinstance(which, list):
                which = which[0]

            input = (input.sort_values('date')
                  .drop_duplicates('where', keep='last')
                  .drop_duplicates(['where', which])
                  .sort_values(by=which, ascending=False)
                  .reset_index(drop=True))

            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_hist

    #####SEABORN PLOT#########
    @decoplotseaborn
    def seaborn_date_plot(self, **kwargs):
        """Create a seaborn line plot with date on x-axis and which on y-axis."""
        input = kwargs['input']
        list(input['where'].unique())
        what = kwargs['what']
        plt = kwargs.get('plt')
        # legend = kwargs.get('legend',None)
        sns = kwargs.get('sns')
        st={k:i for k,i in  enumerate(['-','--',':'])}
        df = input.copy()
        for idx, i in enumerate(what):
            df[f"legend_{i}"] = [kwargs['dicodisplayloc'][w] for w in input['where']]
            #label_col = f'where_{i}'
            #df[label_col] = df['where']
            sns.lineplot(
                data=df,
                x="date",
                y=i,
                linestyle=st[idx],
                hue=f"legend_{i}"
            )
        plt.legend(title=", ".join(what),ncol=len(what))
        plt.xlabel('date')
        plt.xticks(rotation=45)

    @decoplotseaborn
    def seaborn_yearly_plot(self, **kwargs):
        """Draw one curve per calendar year, against the day of the year.

        Superimposes the years so their shapes can be compared directly. The
        29th of February is dropped, so that a given day number means the same
        date in a leap year and a common one.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input', 'what' (a
            single variable) and the 'plt' and 'sns' supplied by the
            decorator.
        """
        input = kwargs['input']
        what = kwargs['what'][0]
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)

        years = sorted(input["allyears"].unique())
        palette = sns.color_palette("husl", n_colors=len(years))
        for color, i in zip(palette, years):
            subset = input.loc[input["allyears"] == i]
            sns.lineplot(
                data=subset,
                x="dayofyear",
                y=what,
                label=str(i),    # la légende affichera les années
                color=color
            )
        plt.title(title)
        plt.xlabel("Day of year")
        plt.ylabel(what)
        plt.legend(title="year", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

    @decoplotseaborn
    def seaborn_versus_plot(self, **kwargs):
        """Plot one variable against another, rather than against time.

        Takes exactly two variables, the first on the x axis and the second on
        the y axis, one line per location.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input', 'what' (two
            variables) and the 'plt' and 'sns' supplied by the decorator.
        """
        input = kwargs['input']
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        sns.lineplot(data=input, x=what[0], y=what[1], hue='where',color='colors')
        plt.legend(title = "where", loc= "upper right",bbox_to_anchor=(1.04, 1))
        plt.xlabel(what[0])
        plt.ylabel(what[1])

    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist_value(self, **kwargs):
        """Create a seaborn vertical histogram where the x-axis represents a numerical field."""
        input = kwargs['input']
        what = kwargs['what']
        sns = kwargs.get('sns')
        plt = kwargs.get('plt')
        sns.set_theme(style="whitegrid")
        sns.histplot(data=input, x=what, bins=24, color='blue', kde=True)
        plt.xlabel(what)
        plt.ylabel('Frequency')

    ######SEABORN HIST HORIZONTALE#########
    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist_horizontal(self, **kwargs):
        """Create a seaborn horizontal histogram with which on x-axis."""
        input = kwargs['input']
        what = kwargs['what']
        # title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        # legend = kwargs.get('legend',None)
        sns.set_theme(style="whitegrid")
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input['where'] = 'sum all location'
        input['where'] = [kwargs['dicodisplayloc'][w] for w in input['where']]
        sns.barplot(data=input, x=what, y='where', palette="viridis", errorbar=None)
        #plt.title(title)
        plt.xlabel(what)
        plt.ylabel('')
        plt.xticks(rotation=45)


    ######SEABORN BOXPLOT#########
    @decoplotseaborn
    def seaborn_pie(self, **kwargs):
        """Create a seaborn pairplot."""
        # input = kwargs['input']
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        plt.xlabel(what)
        plt.ylabel('')
        plt.xticks(rotation=45)

    ######SEABORN heatmap#########
    @decoplotseaborn
    def seaborn_heatmap(self, **kwargs):
        """Create a seaborn heatmap."""
        PyvoaWarning("BEWARE !!! THIS visualisation need to be checked !!!")
        input = kwargs.get('input')
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')

        input['month'] = [m.month for m in input['date']]
        input['year'] = [m.year for m in input['date']]

        data_pivot = input.pivot_table(index='month', columns='year', values=what)

        total = data_pivot.sum().sum()

        sns.heatmap(data_pivot, annot=True, fmt=".1f", linewidths=.5, cmap='plasma')
        plt.xlabel('Year')
        plt.ylabel('Month')

        # Afficher le total en dehors du graphique
        plt.text(0, data_pivot.shape[0] + 1, f'Total: {total}', fontsize=12)
