import csv
import os
import sys
import importlib

settings = importlib.import_module('algorithms.execution.3x3.settings')

# Sync settings
scenarios = settings.scenarios
networks = settings.networks
ingress = settings.ingress
algos = settings.algos
metric_sets = settings.metric_sets
metrics2index = settings.metrics2index

# Custom settings
runs = [str(x) for x in range(0, 50)]
scenarios = ['hc', 'lnc']
networks = ['dfn_58.graphml']
ingress = ['0.1', '0.2', '0.3', '0.4', '0.5']
# ingress = ['0.1']
algos = ['gpasp', 'spr2']
# algos = ['bjointsp', 'bjointsp_recalc']
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


def get_last_row(content):
    return content[-1]


def collect_data():
    data = {}
    for r in runs:
        data[r] = {}
        for s in scenarios:
            data[r][s] = {}
            for net in networks:
                data[r][s][net] = {}
                for ing in ingress:
                    data[r][s][net][ing] = {}
                    for a in algos:
                        last_row = get_last_row(read_output_file(f'scenarios/{r}/{s}/{net}/{ing}/{a}/metrics.csv'))
                        if last_row[0] == '1000':
                            data[r][s][net][ing][a] = last_row
                        else:
                            print(f'Experiment {r}/{s}/{net}/{ing}/{a} did not complete. Last time is {last_row[0]} '
                                  f'instead of 1000. Skipping...')
    return data


def calc_percent_successful_flows(data):
    """Reading the successful and dropped flows, calculate the percent of successful flows. Ignore in-network flows."""
    for r in runs:
        for s in scenarios:
            for net in networks:
                for ing in ingress:
                    for a in algos:
                        if r in data and s in data[r] and net in data[r][s] and ing in data[r][s][net] and a in data[r][s][net][ing]:
                            # calc percentage: succ / (succ + dropped); ignore in network here
                            perc_succ = 0
                            succ = int(data[r][s][net][ing][a][metrics2index['successful_flows']])
                            dropped = int(data[r][s][net][ing][a][metrics2index['dropped_flows']])
                            if succ + dropped > 0:
                                perc_succ = succ / (succ + dropped)
                            # append to data
                            data[r][s][net][ing][a].append(perc_succ)
    return data


def average_data(data):
    avg_data = {}
    for s in scenarios:
        avg_data[s] = {}
        for net in networks:
            avg_data[s][net] = {}
            for ing in ingress:
                avg_data[s][net][ing] = {}
                for a in algos:
                    avg_data[s][net][ing][a] = []
                    for m in range(15):
                        sum = 0
                        for r in runs:
                            sum += float(data[r][s][net][ing][a][m])
                        avg_data[s][net][ing][a].append(sum / len(runs))
    return avg_data


def transform_data(avg_data, metric_set, metric_set_id):
    for s in scenarios:
        for net in networks:
            os.makedirs(f'transformed/{s}/{net}/{metric_set_id}/', exist_ok=True)
            with open(f'transformed/{s}/{net}/{metric_set_id}/t-metrics.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for a in algos:
                    for ing in ingress:
                        for m in metric_set:
                            # x(ing), y(value), hue(metric), style(algo)
                            row = [ing, avg_data[s][net][ing][a][metrics2index[m]], f'{m}', f'{a}']
                            writer.writerow(row)


def transform_data_confidence_intervall(data, metric_set, metric_set_id):
    for s in scenarios:
        for net in networks:
            os.makedirs(f'transformed/{s}/{net}/{metric_set_id}/', exist_ok=True)
            with open(f'transformed/{s}/{net}/{metric_set_id}/ci-t-metrics.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for r in runs:
                    for a in algos:
                        for ing in ingress:
                            if r in data and s in data[r] and net in data[r][s] and ing in data[r][s][net] and a in data[r][s][net][ing]:
                                for m in metric_set:
                                    # x(ing), y(value), hue(metric), style(algo)
                                    row = [ing, data[r][s][net][ing][a][metrics2index[m]], f'{m}', f'{a}']
                                    writer.writerow(row)


def main():
    data = collect_data()
    # avg_data = average_data(data)
    data = calc_percent_successful_flows(data)
    for key, value in metric_sets.items():
        # transform_data(avg_data, value, key)
        transform_data_confidence_intervall(data, value, key)
    print('')


if __name__ == "__main__":
    main()
