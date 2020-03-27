import logging
import os
import yaml
import pathlib
import networkx as nx
import numpy as np
from datetime import datetime
from collections import defaultdict
from siminterface.simulator import ExtendedSimulatorAction
from siminterface.simulator import Simulator
from auxiliary.link import Link
from auxiliary.placement import Placement
from bjointsp.main import place as bjointsp_place
from bjointsp.read_write.reader import read_template

log = logging.getLogger(__name__)


class BJointSPAlgo:
    """
    Global algorithm using B-JointSP
    Decide globally where to process and how to route flows when they arrive at the ingress.
    Then just forward and execute.
    """

    def __init__(self, simulator: Simulator):
        # Besides interaction we need the simulator reference to query all needed information. Not all information can
        # conveniently put into the simulator state, nevertheless it is justified that the algorithm can access these.
        self.simulator = simulator
        # To evaluate if some operations are feasible we need to modify the network topology, that must not happen on
        # the shared network instance

        # require the manipulation of the network topology, we
        self.network_copy = None
        # Timeout determines after which period a unused vnf is removed from a node
        self.vnf_timeout = 10

        # bjointsp: set service templates paths (hard coded!)
        self.sfc_templates = self.load_sfc_templates()

    def load_sfc_templates(self):
        """Load and return dict with SFC templates for B-JointSP"""
        # TODO: when testing with another algorithm, this needs to be adjusted!
        this_dir = pathlib.Path(__file__).parent.absolute()
        with open(os.path.join(this_dir, 'service_templates/sfc_1.yaml')) as f:
            sfc1 = yaml.load(f, Loader=yaml.FullLoader)
        with open(os.path.join(this_dir, 'service_templates/sfc_2.yaml')) as f:
            sfc2 = yaml.load(f, Loader=yaml.FullLoader)
        with open(os.path.join(this_dir, 'service_templates/sfc_3.yaml')) as f:
            sfc3 = yaml.load(f, Loader=yaml.FullLoader)
        sfc_templates = {
            'sfc_1': sfc1,
            'sfc_2': sfc2,
            'sfc_3': sfc3
        }
        return sfc_templates

    def init(self, network_path, service_functions_path, config_path, seed, output_id, resource_functions_path=""):
        # normal setup
        callbacks = {'pass_flow': self.pass_flow, 'init_flow': self.init_flow, 'post_forwarding': self.post_forwarding,
                     'periodic': [(self.periodic_measurement, 100, 'State measurement.'),
                                  (self.periodic_remove, 10, 'Remove SF interception.')]}

        init_state = self.simulator.init(network_path, service_functions_path, config_path, seed, output_id,
                                         resource_functions_path=resource_functions_path,
                                         interception_callbacks=callbacks)

        log.info(f'Network Stats after init(): {init_state.network_stats}')
        self.network_copy = self.simulator.get_network_copy()

        # bjointsp
        self.network_path = network_path

    def run(self):
        placement = defaultdict(list)
        processing_rules = defaultdict(lambda : defaultdict(list))
        forwarding_rules = defaultdict(dict)
        action = ExtendedSimulatorAction(placement=placement, scheduling={}, flow_forwarding_rules=forwarding_rules,
                                         flow_processing_rules=processing_rules)
        self.simulator.apply(action)
        log.info(f'Start simulation at: {datetime.now().strftime("%H-%M-%S")}')
        self.simulator.run()
        log.info(f'End simulation at: {datetime.now().strftime("%H-%M-%S")}')
        log.info(f'Network Stats after run(): {self.simulator.get_state().network_stats}')

    def create_source_list(self, flow):
        """Create and return list of dict of flow source to be passed as input to B-JointSP. Increment flow counter."""
        src_dict = {
            'node': flow.current_node_id,
            'vnf': 'vnf_user',
            'flows': [{
                'id': flow.flow_id,
                'data_rate': flow.dr
            }]
        }
        return [src_dict]

    def init_flow(self, flow):
        """
        Callback when new flow arrives.
        """
        template = self.sfc_templates[flow.sfc]
        source = self.create_source_list(flow)
        result = bjointsp_place(self.network_path, template, source, source_template_object=True,
                                networkx=self.network_copy, write_result=False)

        # save bjointsp's placement & routing in flow state/metadata
        # placement: SF name --> SF placement node
        placement = {}
        for vnf in result['placement']['vnfs']:
            placement[vnf['name']] = vnf['node']
        flow['placement'] = placement
        # routing: link src --> link dest
        # TODO: is this all we need? could one src send to multiple dests based on arc?
        routing = {}
        for link in result['placement']['links']:
            routing[link['link_src']] = link['link_dst']
        flow['routing'] = routing

    def pass_flow(self, flow):
        """
        Callback when flow arrives at a node.
        Here, the flow should be just processed or forwarded as decided at the beginning (see flow state).
        """
        state = self.simulator.get_state()

        # TODO: check if processing flow locally --> process
        # process flow here?
        if flow['placement'][flow.current_sf] == flow.current_node_id:
            log.info(f'Processing flow {flow.flow_id} at node {flow.current_node_id}.')
            # TODO: implement processing

        # TODO: else forward according to selected route
        else:
            if flow.current_node_id == flow.egress_node_id:
                log.info(f'Flow {flow.flow_id} reached its egress {flow.egress_node_id}.')
            else:
                self.forward_flow(flow, state)

        self.simulator.apply(state.derive_action())

    def forward_flow(self, flow, state):
        """
        Forward flow according to saved path. If not possible due to congestion, drop flow.
        """
        # TODO: adjust to bjointsp's routing decisions
        node_id = flow.current_node_id
        assert len(flow['path']) > 0
        next_neighbor_id = flow['path'].pop(0)
        edge = self.simulator.params.network[node_id][next_neighbor_id]

        # Can forward?
        if edge['remaining_cap'] >= flow.dr:
            # yes => set forwarding rule
            state.flow_forwarding_rules[node_id][flow.flow_id] = next_neighbor_id
        # else drop
        # TODO: should I implement the same adaptive shortest path as in the distributed algos here?
        else:
            flow['state'] = 'drop'
            flow['path'] = []
            flow['death_cause'] = 'Forward: The link on the planned path is congested.'

    def periodic_measurement(self):
        """
        <Callback>
        Called periodically to capture the simulator state.
        """
        state = self.simulator.write_state()

    def periodic_remove(self):
        """
         <Callback>
         Called periodically to check if vnfs have to be removed.
        """
        # standard code
        # state = self.simulator.get_state()
        # for node_id, node_data in state.network['nodes'].items():
        #     for sf, sf_data in node_data['available_sf'].items():
        #         if (sf_data['load'] == 0) and ((state.simulation_time - sf_data['last_requested']) > self.vnf_timeout):
        #             state.placement[node_id].remove(sf)
        # self.simulator.apply(state.derive_action())
        pass

    def post_forwarding(self, node_id, flow):
        """
        <Callback>
        Called to remove no longer used forwarding rules, keep it overseeable.
        """
        # Direct access for speed gain
        self.simulator.params.flow_forwarding_rules[node_id].pop(flow.flow_id, None)

    def depart_flow(self, flow):
        """
        <Callback>
        Called to record custom metrics.
        """
        self.metrics.processed_flow(flow)

    def drop_flow(self, flow):
        """
        <Callback>
        Called to record custom metrics.
        """
        self.metrics.dropped_flow(flow)
