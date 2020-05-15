config = ['hc_0.3+']
networks = ['gts_ce_149.graphml']
algos = ['gpasp', 'spr1', 'spr2']

metric_sets = {'flow': ['total_flows', 'successful_flows', 'dropped_flows', 'in_network_flows', 'perc_successful_flows'],
               'delay': ['avg_path_delay_of_processed_flows', 'avg_ingress_2_egress_path_delay_of_processed_flows',
                         'avg_end2end_delay_of_processed_flows'],
               'delay_min': ['avg_path_delay_of_processed_flows', 'avg_ingress_2_egress_path_delay_of_processed_flows'],
               'load': ['avg_node_load', 'avg_link_load'],
               'delay_other': ['avg_end2end_delay_of_processed_flows', 'avg_end2end_delay_of_dropped_flows']
               }

metrics2index = {'time': 0,
                 'total_flows': 1,
                 'successful_flows': 2,
                 'dropped_flows': 3,
                 'in_network_flows': 4,
                 'avg_end2end_delay_of_dropped_flows': 5,
                 'avg_end2end_delay_of_processed_flows': 6,
                 'avg_sf_processing_delay': 7,
                 'avg_sfc_length': 8,
                 'avg_crossed_link_delay': 9,
                 'avg_path_delay': 10,
                 'avg_path_delay_of_processed_flows': 11,
                 'avg_ingress_2_egress_path_delay_of_processed_flows': 12,
                 'avg_node_load': 13,
                 'avg_link_load': 14,
                 'perc_successful_flows': 15
                 }