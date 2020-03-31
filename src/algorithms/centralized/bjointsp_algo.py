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
        self.sfs = self.load_sfs(self.sfc_templates)

    def load_sfc_templates(self):
        """Load and return dict with SFC templates for B-JointSP"""
        # TODO: when testing with other SFCs, this needs to be adjusted!
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

    def load_sfs(self, templates):
        """Create and return set of SFs in the templates. Set = no duplicates"""
        sfs = set()
        for t_name, t in templates.items():
            sfs.update([vnf['name'] for vnf in t['vnfs']])
        return sfs

    def init(self, network_path, service_functions_path, config_path, seed, output_id, resource_functions_path=""):
        # normal setup
        callbacks = {'pass_flow': self.pass_flow, 'init_flow': self.init_flow, 'post_forwarding': self.post_forwarding,
                     'periodic': [(self.periodic_measurement, 100, 'State measurement.'),
                                  (self.periodic_remove, 10, 'Remove SF interception.')]}

        init_state = self.simulator.init(network_path, service_functions_path, config_path, seed, output_id,
                                         resource_functions_path=resource_functions_path,
                                         interception_callbacks=callbacks)

        log.info(f'Network Stats after init(): {init_state.network_stats}')
        # TODO: that won't work. we need to copy before each bjointsp call to get the current resources
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

    def create_sink_list(self, flow):
        """Create and return list with fixed location of sinks 'vnf_sink'"""
        sink_dict = {'node': flow.egress_node_id, 'vnf': 'vnf_sink'}
        return [sink_dict]

    def extract_sf_sink(self, arc):
        """Extract and return sink SF from arc string. Eg, c.0->vnf_sink.0 should return vnf_sink"""
        # remove port ('.0') and split
        arc_clean = arc.replace('.0', '')
        sf_list = arc_clean.split('->')
        # return sink (2nd vnf)
        return sf_list[1]

    def init_flow(self, flow):
        """
        Callback when new flow arrives.
        """
        template = self.sfc_templates[flow.sfc]
        source = self.create_source_list(flow)
        sink = self.create_sink_list(flow)
        # FIXME: make sure self.network_copy is up to date (or use self.network directly if bjointsp doesn't change it)
        # FIXME: adjust bjointsp to use 'remaining_cap' instead of 'cap' to extract caps (adjustable)
        result = bjointsp_place(self.network_path, template, source, source_template_object=True, fixed_vnfs=sink,
                                networkx=self.network_copy, write_result=False)

        # save bjointsp's placement & routing in flow state/metadata
        # placement: SF name --> SF placement node
        placement = {}
        for vnf in result['placement']['vnfs']:
            placement[vnf['name']] = vnf['node']
        flow['placement'] = placement
        # routing: SF --> (link src --> link dest)
        routing = {sf: {} for sf in self.sfs}
        for link in result['placement']['links']:
            sf_sink = self.extract_sf_sink(link['arc'])
            routing[sf_sink][link['link_src']] = link['link_dst']
        flow['routing'] = routing

    def pass_flow(self, flow):
        """
        Callback when flow arrives at a node.
        Here, the flow should be just processed or forwarded as decided at the beginning (see flow state).
        """
        state = self.simulator.get_state()

        # flows that are fully processed are forwarded to their egress without further processing
        if flow.is_processed():
            # set current_sf to "vnf_sink" for fully processed flows. necessary for routing to egress
            flow.current_sf = 'vnf_sink'
            if flow.egress_node_id != flow.current_node_id:
                self.forward_flow(flow, state)

        else:
            # process flow here?
            if flow['placement'][flow.current_sf] == flow.current_node_id:
                log.info(f'Processing flow {flow.flow_id} at node {flow.current_node_id}.')
                # process locally
                state.flow_processing_rules[flow.current_node_id][flow.flow_id] = [flow.current_sf]
                # place SF if it doesn't exist yet
                if flow.current_sf not in state.placement[flow.current_node_id]:
                    state.placement[flow.current_node_id].append(flow.current_sf)

            # else forward flow
            else:
                self.forward_flow(flow, state)

        self.simulator.apply(state.derive_action())

    def forward_flow(self, flow, state):
        """
        Forward flow according to saved path. If not possible due to congestion, drop flow.
        """
        next_neighbor_id = flow['routing'][flow.current_sf][flow.current_node_id]
        edge = self.simulator.params.network[flow.current_node_id][next_neighbor_id]

        # Can forward?
        if edge['remaining_cap'] >= flow.dr:
            # yes => set forwarding rule
            log.info(f'Forwarding flow {flow.flow_id} from {flow.current_node_id} to {next_neighbor_id}.')
            state.flow_forwarding_rules[flow.current_node_id][flow.flow_id] = next_neighbor_id
        # else drop
        # TODO: should I implement the same adaptive shortest path as in the distributed algos here?
        else:
            log.info(f'Dropping flow {flow.flow_id} at {flow.current_node_id} because the link to {next_neighbor_id} '
                     f'is overloaded')
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
        self.simulator.params.flow_forwarding_rules[node_id].pop(flow.flow_id, None)


def main():
    # for testing and debugging
    # Simulator params
    network = 'abilene_11.graphml'
    args = {
        'network': f'../../../params/networks/{network}',
        'service_functions': '../../../params/services/3sfcs.yaml',
        'config': '../../../params/config/simple_config.yaml',
        'seed': 9999,
        'output_path': f'bjointsp-out/{network}'
    }

    # Setup logging
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs(f'{args["output_path"]}/logs', exist_ok=True)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('bjointsp').setLevel(logging.WARNING)
    logging.getLogger('coordsim').setLevel(logging.INFO)
    logging.getLogger('coordsim.reader').setLevel(logging.WARNING)
    simulator = Simulator(test_mode=True)

    # Setup algorithm
    algo = BJointSPAlgo(simulator)
    algo.init(os.path.abspath(args['network']),
              os.path.abspath(args['service_functions']),
              os.path.abspath(args['config']),
              args['seed'],
              args['output_path'])
    # Execute orchestrated simulation
    algo.run()


if __name__ == "__main__":
    main()
