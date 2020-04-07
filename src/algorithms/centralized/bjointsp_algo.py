import logging
import os
import yaml
import pathlib
import time
from datetime import datetime
from collections import defaultdict
from siminterface.simulator import ExtendedSimulatorAction
from siminterface.simulator import Simulator
from auxiliary.placement import Placement
from bjointsp.main import place as bjointsp_place

log = logging.getLogger(__name__)


class BJointSPAlgo:
    """
    Global algorithm using B-JointSP
    Decide globally where to process and how to route flows when they arrive at the ingress.
    Then just forward and execute.
    """

    def __init__(self, simulator: Simulator, recalc_before_drop=False):
        """
        Create B-JointSP algo object.
        @param simulator: Simulator reference to query all needed information
        @param recalc_before_drop: Whether or not to recalculate placement and routing (by calling B-JointSP again)
        for a flow that is about to be dropped due to lack of node resources. Default: False
        """
        self.simulator = simulator

        # bjointsp: set service templates paths (hard coded!)
        self.sfc_templates = self.load_sfc_templates()
        self.sfs = self.load_sfs(self.sfc_templates)
        self.recalc_before_drop = recalc_before_drop

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
        self.network_path = network_path
        
        # normal setup
        callbacks = {'pass_flow': self.pass_flow, 'init_flow': self.init_flow, 'post_forwarding': self.post_forwarding,
                     'periodic': [(self.periodic_measurement, 100, 'State measurement.')]}

        init_state = self.simulator.init(network_path, service_functions_path, config_path, seed, output_id,
                                         resource_functions_path=resource_functions_path, 
                                         interception_callbacks=callbacks)
        log.info(f'Network Stats after init(): {init_state.network_stats}')

        # measure decisions
        # decision in case of bjointsp = "init_flow". flow id --> (node id --> list of times)
        # attention: needs lots of memory when running long!
        self.decision_times = defaultdict(lambda: defaultdict(list))

    def run(self):
        action = ExtendedSimulatorAction(placement=defaultdict(list), scheduling={}, 
                                         flow_forwarding_rules=defaultdict(dict),
                                         flow_processing_rules=defaultdict(lambda : defaultdict(list)))
        self.simulator.apply(action)
        log.info(f'Start simulation at: {datetime.now().strftime("%H-%M-%S")}')
        self.simulator.run()
        log.info(f'End simulation at: {datetime.now().strftime("%H-%M-%S")}')
        log.info(f'Network Stats after run(): {self.simulator.get_state().network_stats}')
        log.info(f"Writing aggregated decisions to {self.simulator.writer.agg_decisions_file_name}")
        self.simulator.writer.write_decision_times(self.decision_times)

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
        start = time.time()
        # call bjointsp to calculate placement and routing for the new flow
        template = self.sfc_templates[flow.sfc]
        source = self.create_source_list(flow)
        sink = self.create_sink_list(flow)
        result = bjointsp_place(self.network_path, template, source, source_template_object=True, fixed_vnfs=sink,
                                networkx=self.simulator.network, networkx_cap='remaining_cap', write_result=False,
                                print_best=False)
        if result is None:
            log.warning(f"Could not compute placement & routing for flow {flow.flow_id}. Dropping it.")
            flow['state'] = 'drop'
            flow['placement'] = {}
            flow['routing'] = {}
            # clear rules belonging to flow
            self.simulator.params.flow_processing_rules[flow.current_node_id].pop(flow.flow_id, None)
            self.simulator.params.flow_forwarding_rules[flow.current_node_id].pop(flow.flow_id, None)
        else:
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

        # record decision time
        decision_time = time.time() - start
        # all done centrally at one logical global node for Bjointsp
        self.decision_times[flow.flow_id]['global'].append(decision_time)

    def remove_rules(self, flow, state):
        """Remove specified flow from the forwarding and processing rules. Remove in place & return."""
        log.debug(f"Removing all forwarding and processing rules for flow {flow.flow_id}")
        # removing from forwarding rules
        for rule in state.flow_forwarding_rules.values():
            rule.pop(flow.flow_id, None)
        # remove from processing rules
        for rule in state.flow_processing_rules.values():
            rule.pop(flow.flow_id, None)
        return state

    def routing_to_sf(self, flow):
        """
        Set routing rules for the given flow to its current SF. By copying rules for previous SFs.
        Necessary when calling B-JointSP again due to lack of node resources.
        Then, it recomputes a new path, but starts again from the source VNF. But the flow may already be at another VNF.
        """
        sfc = self.sfc_templates[flow.sfc]
        # get ordered list of sfs
        sf_order = [vnf['name'] for vnf in sfc['vnfs']]
        # copy routing for all previous SFs
        for sf in sf_order:
            # stop at the current SF
            if sf == flow.current_sf:
                return
            if flow.current_sf in flow['routing']:
                flow['routing'][flow.current_sf].update(flow['routing'][sf])

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
            if flow.current_sf in flow['placement'] and flow['placement'][flow.current_sf] == flow.current_node_id:
                node = state.network['nodes'][flow.current_node_id]
                demand_p, _ = Placement.calculate_demand(flow, flow.current_sf, node['available_sf'],
                                                         self.simulator.params.sf_list)

                if node['capacity'] >= demand_p:
                    log.info(f'Processing flow {flow.flow_id} at node {flow.current_node_id}.')
                    # process locally
                    state.flow_processing_rules[flow.current_node_id][flow.flow_id] = [flow.current_sf]
                    # place SF if it doesn't exist yet
                    if flow.current_sf not in state.placement[flow.current_node_id]:
                        state.placement[flow.current_node_id].append(flow.current_sf)
                # what to do if there's not enough node cap?
                else:
                    log.warning(f"Not enough resources at {flow.current_node_id} to process flow {flow.flow_id}.")
                    if self.recalc_before_drop:
                        log.info(f"Recalculating placement and routing for flow {flow.flow_id} with B-JointSP.")
                        # remove existing rules for the flow
                        state = self.remove_rules(flow, state)
                        # call bjointsp and recalculate placement and routing and pass flow again
                        self.init_flow(flow)
                        # set routing rules to get to next SF
                        self.routing_to_sf(flow)
                        self.pass_flow(flow)

            # else forward flow
            else:
                self.forward_flow(flow, state)

        self.simulator.apply(state.derive_action())

    def forward_flow(self, flow, state):
        """
        Forward flow according to saved path. If not possible due to congestion, drop flow.
        """
        if flow.current_sf not in flow['routing'] or flow.current_node_id not in flow['routing'][flow.current_sf]:
            log.warning(f'Dropping flow {flow.flow_id} because it is missing routing information. Maybe on purpose?')
            flow['state'] = 'drop'
            return

        next_neighbor_id = flow['routing'][flow.current_sf][flow.current_node_id]
        edge = self.simulator.params.network[flow.current_node_id][next_neighbor_id]

        # Can forward?
        if edge['remaining_cap'] >= flow.dr:
            # yes => set forwarding rule
            log.info(f'Forwarding flow {flow.flow_id} from {flow.current_node_id} to {next_neighbor_id}.')
            state.flow_forwarding_rules[flow.current_node_id][flow.flow_id] = next_neighbor_id
        # else drop
        else:
            # TODO: call bjointsp again? call up to X times before dropping a flow?
            log.warning(f'Dropping flow {flow.flow_id} at {flow.current_node_id} because the link to '
                        f'{next_neighbor_id} is overloaded')
            flow['state'] = 'drop'

    def periodic_measurement(self):
        """
        <Callback>
        Called periodically to capture the simulator state.
        """
        state = self.simulator.write_state()

    def post_forwarding(self, node_id, flow):
        """
        <Callback>
        Called to remove no longer used forwarding rules, keep it overseeable.
        """
        self.simulator.params.flow_forwarding_rules[node_id].pop(flow.flow_id, None)


if __name__ == "__main__":
    # for testing and debugging
    # Simple test params
    # network = 'abilene_11.graphml'
    # args = {
    #     'network': f'../../../params/networks/{network}',
    #     'service_functions': '../../../params/services/3sfcs.yaml',
    #     'config': '../../../params/config/simple_config.yaml',
    #     'seed': 9999,
    #     'output_path': f'bjointsp-out/{network}'
    # }

    # Evaluation params
    network = 'dfn_58.graphml'
    args = {
        'network': f'../../../params/networks/{network}',
        'service_functions': '../../../params/services/3sfcs.yaml',
        'config': '../../../params/config/llc_0.5.yaml',
        'seed': 9999,
        'output_path': f'bjointsp-out/{network}'
    }

    # Setup logging to screen
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('bjointsp').setLevel(logging.WARNING)
    logging.getLogger('coordsim').setLevel(logging.INFO)
    logging.getLogger('coordsim.reader').setLevel(logging.WARNING)
    simulator = Simulator(test_mode=True)

    # Setup algorithm
    algo = BJointSPAlgo(simulator, recalc_before_drop=False)
    algo.init(os.path.abspath(args['network']), os.path.abspath(args['service_functions']),
              os.path.abspath(args['config']), args['seed'], args['output_path'])
    # Execute orchestrated simulation
    algo.run()
