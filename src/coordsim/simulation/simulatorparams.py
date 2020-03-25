"""

Flow Simulator parameters.
- Allows for clean and quick access to parameters from the flow simulator.
- Facilitates the quick changing of schedule decisions and
other parameters for the simulator.

"""


class SimulatorParams:
    def __init__(self, network, ing_nodes, eg_nodes, sfc_list, sf_list, config, seed, schedule={}, sf_placement={},
                 flow_forwarding_rules={}, flow_processing_rules={}, interception_callbacks={}):
        # Seed for the random generator: int
        self.seed = seed
        # NetworkX network object: DiGraph
        self.network = network
        # Ingress nodes of the network (nodes at which flows arrive): list
        self.ing_nodes = ing_nodes
        # Possible egress nodes of the network (nodes at which flows may leave the network): list
        self.eg_nodes = eg_nodes
        # List of available SFCs and their child SFs: defaultdict(None)
        self.sfc_list = sfc_list
        # List of every SF and it's properties (e.g. processing_delay): defaultdict(None)
        self.sf_list = sf_list

        # read dummy placement and schedule if specified
        # Flow forwarding schedule: dict
        self.schedule = schedule
        # Placement of SFs in each node: defaultdict(list)
        self.sf_placement = sf_placement
        # Update which sf is available at which node
        for node_id, placed_sf_list in sf_placement.items():
            available_sf = {}
            for sf in placed_sf_list:
                available_sf[sf] = self.network.nodes[node_id]['available_sf'].get(sf, {'load': 0.0})
            self.network.nodes[node_id]['available_sf'] = available_sf

        # Flow forwarding rules
        self.flow_forwarding_rules = flow_forwarding_rules
        # Flow processing rules
        self.flow_processing_rules = flow_processing_rules
        # Callbacks to allow the flowsimulator interact with external functions at certain events
        self.interception_callbacks = interception_callbacks

        # The duration of a run in the simulator's interface
        self.run_duration = config['run_duration']
        # Make complete configuration accessible to allow different parameter modes
        self.sim_config = config

    # string representation for logging
    def __str__(self):
        params_str = "Simulator parameters: \n"
        params_str += "seed: {}\n".format(self.seed)
        return params_str
