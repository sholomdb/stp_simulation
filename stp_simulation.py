from itertools import permutations


class Network:
    def __init__(self, num_of_switches, ports_per_switch):
        self.switches = {}
        for i in range(num_of_switches):
            self.add_switch(i, ports_per_switch[i], 1)

    def add_connections(self, connections):
        for connection in connections:
            all_couple_connections = list(permutations(connection, 2))
            for (switch_id_1, port_num_1), (switch_id_2, port_num_2) in all_couple_connections:
                self.add_connection(self.switches[switch_id_1], port_num_1, self.switches[switch_id_2], port_num_2)

    def add_connection(self, switch_1, port1, switch_2, port2):
        switch_1.add_neighbor(switch_2, port1)
        switch_2.add_neighbor(switch_1, port2)

    def remove_switch(self, switch_id):
        for switch in self.switches.values():
            for port_num in range(switch.num_of_ports):
                switch.neighbors[port_num] = [neighbor for neighbor in switch.neighbors[port_num] if neighbor.id != switch_id]
        del self.switches[switch_id]

    def add_switch(self, switch_id, num_of_ports, weight=1):
        if switch_id in self.switches:
            raise ValueError(f"Switch with id {switch_id} already exists")
        self.switches[switch_id] = Switch(switch_id, num_of_ports, weight)

    def run_sycl(self):
        for switch in self.switches.values():
            switch.run_sycl()

    def __str__(self):
        return "\n".join([str(switch) for switch in self.switches.values()])


class Switch:
    def __init__(self, switch_id, num_of_ports, weight=1):
        self.id = switch_id
        self.num_of_ports = num_of_ports
        self.neighbors = [[] for _ in range(num_of_ports)]
        self.pots_status = [True] * num_of_ports

        # hello parameters
        self.root_id = switch_id
        self.dist_from_root = 0
        self.root_port = -1
        self.closest_switch = switch_id
        self.weight = weight

    def add_neighbor(self, neighbor_switch, port_num):
        self.neighbors[port_num].append(neighbor_switch)

    def run_sycl(self):
        hello_messages = []
        for port_num in range(self.num_of_ports):
            for neighbor_switch in self.neighbors[port_num]:
                root_id, dist_from_root, neighbor_id = neighbor_switch.get_hello_message()
                hello_message = (root_id, dist_from_root, neighbor_id, port_num)
                hello_messages.append(hello_message)

        self.update_hello_parameters_by_neighbors(hello_messages)
        self.update_ports_status(hello_messages)

    def reset_hello_parameters(self):
        self.set_hello_parameters(self.id, 0, self.id, -1)

    def update_hello_parameters_by_neighbors(self, hello_messages):
        if not hello_messages:
            self.reset_hello_parameters()
            return
        last_min_message = self.root_id, self.dist_from_root - self.weight, self.closest_switch, self.root_port
        min_message = min(hello_messages)
        if min_message > last_min_message:
            # somthing changed in the network -> time to reset
            self.reset_hello_parameters()
            return
        min_root_id, min_dist_from_id, min_neighbor_id, min_port_num = min_message
        self.set_hello_parameters(min_root_id, min_dist_from_id + self.weight, min_neighbor_id, min_port_num)

    def set_hello_parameters(self, root_id, dist_from_root, closest_switch, root_port):
        self.root_id = root_id
        self.dist_from_root = dist_from_root
        self.closest_switch = closest_switch
        self.root_port = root_port

    def get_hello_message(self):
        return self.root_id, self.dist_from_root, self.id

    def update_ports_status(self, hello_messages):
        for port_num in range(self.num_of_ports):
            port_hello_messages = [message[:3] for message in hello_messages if message[3] == port_num]
            self.update_port_status(port_num, port_hello_messages)

        # if all port but the root port are False then close it too
        if self.pots_status.count(True) == 1:
            self.pots_status[self.pots_status.index(True)] = False

    def update_port_status(self, port_num, port_hello_messages):

        # option 1 - the port is the source path from the root
        is_it_my_root_port = port_num == self.root_port

        # option 2 - this switch is the best supplier for that LAN segment
        my_message = self.get_hello_message()
        min_message = min(port_hello_messages + [my_message])
        min_root_id, min_dist_from_id, min_neighbor_id = min_message
        im_the_best_supplier = min_neighbor_id == self.id

        self.pots_status[port_num] = is_it_my_root_port or im_the_best_supplier

    def __str__(self):
        return (
                f"Switch {self.id}: " +
                f"root_id: {self.root_id} " +
                f"dist_from_root: {self.dist_from_root} " +
                f"root_port: {self.root_port} " +
                f"closest_switch: {self.closest_switch} " +
                f"weight: {self.weight} " +
                f"pots_status: {self.pots_status} "
        )

def run_simulation(iterations, network, padding):
    print(f"{'#' * padding} initial network {'#' * padding}")
    print(network)
    for i in range(iterations):
        print(f"{'#' * padding} iteration {i + 1} {'#' * padding}")
        network.run_sycl()
        print(network)


def main():
    padding = 10
    num_of_switches = 7
    ports_per_switch = [2, 2, 2, 2, 3, 2, 2]
    connections = [
        # format: [(switch_id_1, port1), (switch_id_2, port2) ...]
        [(0, 1), (2, 1)],  # A
        [(0, 0), (1, 1), (5, 1), (4, 2)],  # B
        [(1, 0), (4, 1), (6, 1), (2, 0)],  # C
        [(3, 1), (4, 0), (5, 0)],  # D
        [(3, 0), (6, 0)],  # E
    ]
    network = Network(num_of_switches, ports_per_switch)
    network.add_connections(connections)

    run_simulation(5, network, padding)

    network.remove_switch(0)
    print('\n' * 2 + f"{'#' * padding} after removing switch 0 {'#' * padding}" + '\n' * 2)
    run_simulation(4, network, padding)



if __name__ == "__main__":
    main()
