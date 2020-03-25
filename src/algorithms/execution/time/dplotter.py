import csv
import os
import sys

import pandas as pd
import seaborn as sns
from pandas.plotting import register_matplotlib_converters
import matplotlib.pyplot as plt


pp_algo = {'gpasp': 'GPASP', 'spr1': 'SPR-1', 'spr2': 'SPR-2'}
pp_categories = {'counted': 'Counted', 'total': 'Total'}
pp_network = {'bics_34.graphml': 'BICS', 'dfn_58.graphml': 'DFN', 'intellifiber_73.graphml': 'Intellifiber',
              'gts_ce_149.graphml': 'GTS CE'}

def get_data(data_path):
    table = []
    with open(data_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            table.append(row)

    data = {'Algorithms': [], 'Decisions': [], 'Categories': []}
    for row in table:
        data['Algorithms'].append(pp_algo[row[0]])
        data['Decisions'].append(int(row[1]))
        data['Categories'].append(pp_categories[row[2]])
    return data


def get_test():
    data = {'y': [x for x in range(1, 18)], 'x': ['x' for x in range(1, 18)]}
    return pd.DataFrame(data=data)


def main():
    config = 'hc_0.3+'
    network = 'gts_ce_149.graphml'
    prefix = '0.3 - '

    register_matplotlib_converters()
    sns.set(style="whitegrid", rc={"axes.labelsize":16, "axes.titlesize":16})

    input_path = f'transformed/{config}/{network}/decisions'
    output_path = f'plotted/{config}/{network}/decisions'

    data = get_data(f'{input_path}/t-metrics.csv')
    df = pd.DataFrame(data=data)


    sns_plot = sns.boxenplot(x="Algorithms", y="Decisions", hue="Categories", data=df)
    sns_plot.set_title(f'{prefix}{pp_network[network]}')
    #sns_plot.tick_params(labelsize=16)  # added

    sns_plot.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), shadow=True, ncol=2)
    plt.setp(sns_plot.get_legend().get_texts(), fontsize='16')  # for legend text
    plt.setp(sns_plot.get_legend().get_title(), fontsize='18')  # for legend title

    fig = sns_plot.get_figure()
    os.makedirs(f'{output_path}', exist_ok=True)
    fig.savefig(f'{output_path}/boxenplot.png', bbox_inches='tight')


    plt.clf()
    sns_plot = sns.barplot(x="Algorithms", y="Decisions", hue="Categories", data=df)
    sns_plot.set_title(f'{prefix}{pp_network[network]}')
    #sns_plot.tick_params(labelsize=16)  # added

    sns_plot.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), shadow=True, ncol=2)
    plt.setp(sns_plot.get_legend().get_texts(), fontsize='16')  # for legend text
    plt.setp(sns_plot.get_legend().get_title(), fontsize='18')  # for legend title

    fig = sns_plot.get_figure()
    os.makedirs(f'{output_path}', exist_ok=True)
    fig.savefig(f'{output_path}/barplot.png', bbox_inches='tight')

if __name__ == "__main__":
    main()