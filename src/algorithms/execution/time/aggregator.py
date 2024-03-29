import csv
import os

import algorithms.execution.time.settings as settings

runs = [str(x) for x in range(50)]

# Sync settings
config = settings.config
networks = settings.networks
algos = settings.algos
metric_sets = settings.metric_sets
metrics2index = settings.metrics2index


# Custom settings
runs = [str(x) for x in range(150, 200)]
# config = ['hc_0.3+']
config = ['hc', 'lnc']
# networks = ['gts_ce_149.graphml']
networks = ['dfn_58.graphml']
ing = '0.3'
# algos = ['gpasp', 'spr1', 'spr2']
# algos = ['gpasp', 'spr2']
algos = ['bjointsp', 'bjointsp_recalc']
metric_sets = {'flow': ['total_flows', 'successful_flows', 'dropped_flows', 'in_network_flows', 'perc_successful_flows'],
               'delay': ['avg_end2end_delay_of_processed_flows'],
               'load': ['avg_node_load', 'avg_link_load']}


def read_output_file(path):
    with open(path) as csvfile:
        filereader = csv.reader(csvfile)
        content = []
        for row in filereader:
            content.append(row)
        return content


def remove_first(content):
    return content[1:]


def collect_data():
    data = {}
    for c in config:
        data[c] = {}
        for r in runs:
            data[c][r] = {}
            for net in networks:
                data[c][r][net] = {}
                for a in algos:
                    # data[c][r][net][a] = remove_first(read_output_file(f'scenarios/{c}/{r}/{net}/{a}/metrics.csv'))
                    # for reading 3x3 data, which is structured differently
                    data[c][r][net][a] = remove_first(read_output_file(f'../3x3/scenarios/{r}/{c}/{net}/{ing}/{a}/metrics.csv'))
    return data


def collect_data_decisions():
    data = {}
    for c in config:
        data[c] = {}
        for r in runs:
            data[c][r] = {}
            for net in networks:
                data[c][r][net] = {}
                for a in algos:
                    data[c][r][net][a] = remove_first(read_output_file(f'scenario/{c}/{r}/{net}/{a}/decisions.csv'))
    return data


def calc_percent_successful_flows(data):
    """Reading the successful and dropped flows, calculate the percent of successful flows. Ignore in-network flows."""
    for c in config:
        for r in runs:
            for net in networks:
                for a in algos:
                    for drow in data[c][r][net][a]:
                        # calc percentage: succ / (succ + dropped); ignore in network here
                        perc_succ = 0
                        succ = int(drow[metrics2index['successful_flows']])
                        dropped = int(drow[metrics2index['dropped_flows']])
                        if succ + dropped > 0:
                            perc_succ = succ / (succ + dropped)
                        # append to data
                        drow.append(perc_succ)
    return data


#Deprecated
def collect_data_runs(rconfig, rruns, rnetworks, ring):
    data = {}
    for c in rconfig:
        data[c] = {}
        for r in rruns:
            data[c][r] = {}
            for net in rnetworks:
                data[c][r][net] = {}
                for a in algos:
                    data[c][r][net][a] = remove_first(
                        read_output_file(f'scenario/{r}/{c}/{net}/{ring}/{a}/metrics.csv'))
    return data

#Deprecated
def transform_data_runs(data, rconfig, rruns, rnetworks, metric_set, metric_set_id):
    for c in rconfig:
        for net in rnetworks:
            os.makedirs(f'transformed/{c}/{net}/{metric_set_id}/', exist_ok=False)
            with open(f'transformed/{c}/{net}/{metric_set_id}/t-metrics.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for r in rruns:
                    for a in algos:
                        for drow in data[c][r][net][a]:
                            for m in metric_set:
                                # x(time), y(value), hue(metric), style(algo)
                                row = [drow[metrics2index['time']], drow[metrics2index[m]], f'{m}', f'{a}']
                                writer.writerow(row)


def transform_data(data, metric_set, metric_set_id):
    for c in config:
        for net in networks:
            os.makedirs(f'transformed/{c}/{net}/{metric_set_id}/', exist_ok=False)
            with open(f'transformed/{c}/{net}/{metric_set_id}/t-metrics.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for r in runs:
                    for a in algos:
                        for drow in data[c][r][net][a]:
                            for m in metric_set:
                                # x(time), y(value), hue(metric), style(algo)
                                row = [drow[metrics2index['time']], drow[metrics2index[m]], f'{m}', f'{a}']
                                writer.writerow(row)


def transform_combine_data_decisions(d_data, data):
    for c in config:
        for net in networks:
            os.makedirs(f'transformed/{c}/{net}/decisions/', exist_ok=False)
            with open(f'transformed/{c}/{net}/decisions/t-metrics.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for r in runs:
                    for a in algos:
                        for drow in d_data[c][r][net][a]:
                             # x(algorithm), y(value), hue(categorie)
                            row = [f'{a}', drow[2], 'counted']
                            writer.writerow(row)
                        row = [f'{a}', data[c][r][net][a][-1][metrics2index['total_flows']], 'total']
                        writer.writerow(row)


def main():
    data = collect_data()
    # d_data = collect_data_decisions()
    data = calc_percent_successful_flows(data)
    for key, value in metric_sets.items():
        transform_data(data, value, key)
    # transform_combine_data_decisions(d_data, data)

    # rdata = collect_data_runs(['hc', 'llc', 'lnc'], [str(x) for x in range(40)],
    #                           ['bics_34.graphml', 'dfn_58.graphml', 'intellifiber_73.graphml'], '0.3')
    # for key, value in metric_sets.items():
    #     transform_data_runs(rdata, ['hc', 'llc', 'lnc'], [str(x) for x in range(40)],
    #                         ['bics_34.graphml', 'dfn_58.graphml', 'intellifiber_73.graphml'], value, key)
    print('')


if __name__ == "__main__":
    main()
