"""
Simulator file writer module
"""
import yaml
import csv
import os
import datetime as dt
import pandas as pd
import numpy as np
from spinterface import SimulatorAction, SimulatorState


class ResultWriter():
    """
    Result Writer
    Helper class to write results to CSV files.
    """
    def __init__(self, test_mode: bool, config, simulator_params):
        """
        If the simulator is in test mode, create result folder and CSV files
        """
        self.test_mode = test_mode
        if self.test_mode:
            now = dt.datetime.now()

            self.result_path = simulator_params['output_path']
            self.placement_file_name = f'{self.result_path}/placement.csv'
            self.resources_file_name = f'{self.result_path}/resources.csv'
            self.metrics_file_name = f'{self.result_path}/metrics.csv'
            self.decisions_file_name = f'{self.result_path}/decisions.csv'
            self.agg_decisions_file_name = f'{self.result_path}/agg_decisions.csv'

            # self.result_path = f'{simulator_params["output_id"]}/results/' \
            #     f'{os.path.basename(simulator_params["network"])}/' \
            #     f'run_{now.strftime("%Y-%m-%d_%H-%M-%S")}'
            # "placements_YYYY-MM-DD_hh-mm-ss_<seed>.csv"
            # self.scheduling_file_name = f'{self.result_path}/scheduling_{now.strftime("%Y-%m-%d_%H-%M-%S")}.csv'
            # self.placement_file_name = f'{self.result_path}/placements_{now.strftime("%Y-%m-%d_%H-%M-%S")}.csv'
            # self.resources_file_name = f'{self.result_path}/resources_{now.strftime("%Y-%m-%d_%H-%M-%S")}.csv'
            # self.metrics_file_name = f'{self.result_path}/metrics_{now.strftime("%Y-%m-%d_%H-%M-%S")}.csv'

            # Create the results directory if not exists
            os.makedirs(self.result_path, exist_ok=True)

            # Save configuration to reconstruct the parameters
            #with open(f'{self.result_path}/config_{now.strftime("%Y-%m-%d_%H-%M-%S")}.yml', 'w') as outfile:
            #with open(f'{self.result_path}/config_{now.strftime("%Y-%m-%d_%H-%M-%S")}.yml', 'w') as outfile:
            #    yaml.dump(config, outfile, default_flow_style=False)
            #    yaml.dump(simulator_params, outfile, default_flow_style=False)

            self.placement_stream = open(self.placement_file_name, 'w', newline='')
            # self.scheduling_stream = open(self.scheduling_file_name, 'a+', newline='')
            self.resources_stream = open(self.resources_file_name, 'w', newline='')
            self.metrics_stream = open(self.metrics_file_name, 'w', newline='')
            self.decisions_stream = open(self.decisions_file_name, 'w', newline='')

            # Create CSV writers
            self.placement_writer = csv.writer(self.placement_stream)
            # self.scheduling_writer = csv.writer(self.scheduling_stream)
            self.resources_writer = csv.writer(self.resources_stream)
            self.metrics_writer = csv.writer(self.metrics_stream)
            self.decisions_writer = csv.writer(self.decisions_stream)

            # Write the headers to the files
            self.create_csv_headers()

    def create_csv_headers(self):
        """
        Creates statistics CSV headers and writes them to their files
        """

        # Create CSV headers
        # scheduling_output_header = ['time', 'origin_node', 'sfc', 'sf', 'schedule_node', 'schedule_prob']
        placement_output_header = ['time', 'node', 'sf']
        resources_output_header = ['time', 'node', 'node_capacity', 'used_resources']
        # metrics_output_header = ['time', 'total_flows', 'successful_flows', 'dropped_flows', 'in_network_flows',
        #                          'avg_end_2_end_delay']
        metrics_output_header = ['time', 'total_flows', 'successful_flows', 'dropped_flows', 'in_network_flows',
                                 'avg_end2end_delay_of_dropped_flows', 'avg_end2end_delay_of_processed_flows',
                                 'avg_sf_processing_delay', 'avg_sfc_length', 'avg_crossed_link_delay',
                                 'avg_path_delay', 'avg_path_delay_of_processed_flows',
                                 'avg_ingress_2_egress_path_delay_of_processed_flows', 'avg_node_load', 'avg_link_load']
        decisions_output_header = ['time', 'node', 'decisions']

        # Write headers to CSV files
        self.placement_writer.writerow(placement_output_header)
        # self.scheduling_writer.writerow(scheduling_output_header)
        self.resources_writer.writerow(resources_output_header)
        self.metrics_writer.writerow(metrics_output_header)
        self.decisions_writer.writerow(decisions_output_header)

    def write_action_result(self, env, action: SimulatorAction):
        """
        Write simulator actions to CSV files for statistics purposes
        """
        if self.test_mode:
            placement = action.placement
            scheduling = action.scheduling
            time = env.now
            placement_output = []
            scheduling_output = []

            for node_id, sfs in placement.items():
                for sf in sfs:
                    placement_output_row = [time, node_id, sf]
                    placement_output.append(placement_output_row)

            for node, sfcs in scheduling.items():
                for sfc, sfs in sfcs.items():
                    for sf, scheduling in sfs.items():
                        for schedule_node, schedule_prob in scheduling.items():
                            scheduling_output_row = [time, node, sfc, sf, schedule_node, schedule_prob]
                            scheduling_output.append(scheduling_output_row)

            self.placement_writer.writerows(placement_output)
            # self.scheduling_writer.writerows(scheduling_output)

    def write_state_results(self, env, state: SimulatorState):
        """
        Write node resource consumption to CSV file
        """
        if self.test_mode:
            placement = state.placement
            network = state.network
            stats = state.network_stats
            time = env.now

            metrics_output = [int(time), stats['total_flows'], stats['successful_flows'], stats['dropped_flows'],
                              stats['in_network_flows'], stats['avg_end2end_delay_of_dropped_flows'],
                              stats['avg_end2end_delay_of_processed_flows'], stats['avg_sf_processing_delay'],
                              stats['avg_sfc_length'], stats['avg_crossed_link_delay'], stats['avg_path_delay'],
                              stats['avg_path_delay_of_processed_flows'],
                              stats['avg_ingress_2_egress_path_delay_of_processed_flows'], stats['avg_node_load'],
                              stats['avg_link_load']]

            resource_output = []
            for key, node in network['nodes'].items():
                node_id = node['id']
                node_cap = node['capacity']
                used_resources = node['used_capacity']
                resource_output_row = [time, node_id, node_cap, used_resources]
                resource_output.append(resource_output_row)

            placement_output = []
            for node_id, sfs in placement.items():
                for sf in sfs:
                    placement_output_row = [time, node_id, sf]
                    placement_output.append(placement_output_row)

            self.placement_writer.writerows(placement_output)
            self.metrics_writer.writerow(metrics_output)
            self.resources_writer.writerows(resource_output)

    def write_decisions_results(self, env, state: SimulatorState):
        network = state.network
        stats = state.network_stats
        time = env.now

        decisions_output = []
        for key, node in network['nodes'].items():
            node_id = node['id']
            decisions_output_row = [int(time), node_id, stats['decisions'][node_id]]
            decisions_output.append(decisions_output_row)

        self.decisions_writer.writerows(decisions_output)

    def write_decision_times(self, decision_times):
        """New function for writing decision times (avg, std, count) at the end of simulation."""
        # columns: flow ID, node ID, num decisions, avg decision time, std dev decision time
        data = {'flow': [], 'node': [], 'dec_count': [], 'dec_time_avg': [], 'dec_time_std': []}
        for f, node_dict in decision_times.items():
            for v, times in node_dict.items():
                data['flow'].append(f)
                data['node'].append(v)
                data['dec_count'].append(len(times))
                data['dec_time_avg'].append(np.mean(times))
                data['dec_time_std'].append(np.std(times))
        # create df and write to csv
        df = pd.DataFrame(data=data)
        df.to_csv(self.agg_decisions_file_name, index=False)

    def close_streams(self):
        """
        Close open streams
        """
        if self.test_mode:
            self.placement_stream.close()
            # self.scheduling_stream.close()
            self.resources_stream.close()
            self.metrics_stream.close()
            self.decisions_stream.close()

    def __del__(self):
        # Close all writer streams
        self.close_streams()
