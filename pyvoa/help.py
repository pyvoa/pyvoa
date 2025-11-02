import argparse

# Basic metadata
__version__ = '3.0.1'
__author__ = 'Tristan Beau, Julien Browaeys, Olivier Dadoun'
__github__ = 'https://github.com/src.project/pycoa'
__web__ = 'http://pycoa.fr/'

# ANSI color codes
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def display_full_help():
    print()
    print(f"{RED}{BOLD}=== Welcome to the Pysrc Help System ==={RESET}\n")

    # -------------------------
    # Basic commands
    # -------------------------
    print(f"{BLUE}{BOLD}Available Commands:{RESET}\n")
    list_commands = [
        ('listwhom', "List available databases"),
        ('listwhom(True)', "List available databases as a pandas DataFrame (recommended)"),
        ('setwhom(\"DBname\")', "Set the database to be used"),
        ('getwhom', "Display the currently used database"),
        ('listwhich', "List available epidemiological variables"),
        ('listwhere', "List available departments"),
        ('listwhere(True)', "List available regions"),
        ('listwhat', "Show data modes: cumulative, daily, weekly"),
        ('listoption', "List available options"),
        ('listoutput', "List available output formats: pandas, geopandas, list, dict, array"),
        ('listpop', "List normalization options (per population)"),
        ('listplot', "List available plot types"),
        ('listtile', "List available map textures"),
        ('listvisu', "List available visualization options for maps"),
        ('dir(pycoa)', "Display all available methods")
    ]
    for command, description in list_commands:
        print(f"  {GREEN}{command.ljust(30)}{RESET}{description}")
    print()

    # -------------------------
    # Graph commands
    # -------------------------
    print(f"{BLUE}{BOLD}Graph Commands:{RESET}\n")
    graph_commands = [
        ('plot', "Display selected data as a time series"),
        ('map', "Display data as a geographical map"),
        ('hist', "Display data as histograms"),
        ('get', "Retrieve data for further processing")
    ]
    for command, description in graph_commands:
        print(f"  {GREEN}{command.ljust(30)}{RESET}{description}")

        # Plot sub-options
        if command == 'plot':
            plot_options = [
                ("typeofplot='date' (default)", "Time evolution of the selected variable"),
                ("typeofplot='compare'", "Compare two locations over time"),
                ("typeofplot='yearly'", "Compare different years month by month"),
                ("typeofplot='spiral'", "Spiral representation (complementary to yearly)")
            ]
            for opt, desc in plot_options:
                print(f"    {YELLOW}{opt.ljust(35)}{RESET}{desc}")

        # Histogram sub-options
        if command == 'hist':
            hist_options = [
                ("typeofhist='country' (default)", "Histogram by country"),
                ("typeofhist='value'", "Histogram by value"),
                ("typeofhist='pie'", "Pie chart representation")
            ]
            for opt, desc in hist_options:
                print(f"    {YELLOW}{opt.ljust(35)}{RESET}{desc}")
    print()

    # -------------------------
    # Examples
    # -------------------------
    print(f"{BLUE}{BOLD}Examples:{RESET}\n")
    examples = [
        ('listwhich', "pycoa.listwhich()"),
        ('plot', "pycoa.plot(where=['France', 'Italy', 'United Kingdom'])"),
        ('map', "pycoa.map(where='world', what='daily', when='01/04/2020')"),
        ('hist', "pycoa.hist(where='Middle Africa', which='tot_confirmed', what='cumul')"),
        ('get', "pycoa.get(where='USA', what='daily', which='tot_recovered', output='pandas')")
    ]
    for cmd, ex in examples:
        print(f"  {GREEN}{cmd.ljust(30)}{RESET}{BOLD}{ex}{RESET}")
    print()

def main():
    parser = argparse.ArgumentParser(
        description="Extended help for Pysrc.",
        add_help=False
    )

    parser.add_argument('-h', '--help', action='store_true', help="Show the complete Pysrc help.")
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
                        help="Show the current version of Pysrc.")
    parser.add_argument('-a', '--author', action='store_true', help="Show the authors of Pysrc.")
    parser.add_argument('-g', '--github', action='store_true', help="Show the Pysrc GitHub repository.")
    parser.add_argument('-w', '--web', action='store_true', help="Show the Pysrc website.")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        display_full_help()
    elif args.github:
        print(__github__)
    elif args.web:
        print(__web__)
    elif args.author:
        print(__author__)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
