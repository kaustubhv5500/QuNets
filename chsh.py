#!/usr/bin/env python3
#
#  CHSH Game implementation for the course Introduction to Quantum Networks
#
#  Author: Simon Sekavčnik and Course Paricipants
#  Released under GPL-2.0 (GNU General Public License)
#

## IMPORTS
import numpy as np
import random
from threading import Thread, Event
from qunetsim.components import Host
from qunetsim.components import Network
from qunetsim.objects import Qubit
from qunetsim.objects import Logger

## CONSTANTS
STRATEGY_A = [0, np.pi/4]
STRATEGY_B = [np.pi/8, -np.pi/8]

def get_unitary(angle):
    return np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])

class Referee():
    def __init__(self):
        self.host = Host('Referee')
        self.question = None
        self.protocol = None
        self.players = []

    def register_player(self, player):
        self.players.append(player)

    def generate_questions(self):
        self.questions = [random.randint(0,1) for p in self.players]

    def evaluate_answers(self):
        pass

    def protocol(self):
        while True:
            self.generate_questions()
            for i, player in enumerate(self.players):
                player.host.send_classical(player, self.questions[i])

    def run(self):
        self.protocol = Thread(target=protocol)
        self.start()

class Player():
    def __init__(self, strategy, name):
        self.host = Host(name)
        self.strategy = strategy
        self.referee = None
        self.epr_gen = None
        self.qubit = None

    def register_referee(self, referee):
        self.referee = referee
    
    def register_epr(self, epr_gen):
        self.epr_gen = epr_gen

    def request_epr(self):
        self.host.send_classical(self.epr_gen, "0")
        self.host.get_data_qubit(self.epr_gen, wait=1)


    def run(self):
        pass

    def protocol(self):
        while True:
            question = self.host.get_classical(self.referee, wait=-1)[-1]
            question = int(question.content)
            resp = self.request_epr()

            if self.qubit is None:
                pass # Classical strategy
            else:
                pass # Quantum strategy


class EPR_GEN():
    def __init__(self):
        self.host = Host('EPR_GEN')
        self.players = []

    def protocol(self):
        while True:
            for p in self.players:
                self.host.get_classical(p, wait=-1)

    def distribute_epr_pairs(self):
        qubits = [Qubit(self.host) for p in self.players]
        qubits[0].H()
        for q in qubits[1:]:
            qubits[0].cnot(q)
        
        for i, player in enumerate(self.players):
            self.host.send_qubit(player, qubits[i])


    def run(self):
        self.protocol = Thread(target=protocol)
        self.start()
    
    def register_player(self, player):
        self.players.append(player)


def main():
    network = Network.get_instance()

    # Initializing host objects and the network
    ref = Referee()
    alice = Player(STRATEGY_A, 'Alice')
    bob = Player(STRATEGY_B, 'Bob')
    epr = EPR_GEN()

    network.start()

    # Add connections between referee and players in both directions
    ref.host.add_c_connection(alice.host.host_id)
    ref.host.add_c_connection(bob.host.host_id)
    alice.host.add_c_connection(ref.host.host_id)
    bob.host.add_c_connection(ref.host.host_id)

    # Add connections between epr and players in both directions
    epr.host.add_q_connection(alice.host.host_id)
    epr.host.add_q_connection(bob.host.host_id)
    alice.host.add_q_connection(epr.host.host_id)
    bob.host.add_q_connection(epr.host.host_id)

    # Starting the host nodes
    ref.host.start()
    alice.host.start()
    bob.host.start()
    epr.host.start()

    # Adding hosts to the network
    network.add_host(ref.host)
    network.add_host(alice.host)
    network.add_host(bob.host)
    network.add_host(epr.host)

    # Registers players with the referee and vice versa
    ref.register_player(alice.host.host_id)
    ref.register_player(bob.host.host_id)

    alice.register_referee(ref.host.host_id)
    bob.register_referee(ref.host.host_id)

    alice.register_epr(epr.host.host_id)
    bob.register_epr(epr.host.host_id)

    epr.register_player(alice.host.host_id)
    epr.register_player(bob.host.host_id)


if __name__ == "__main__":
    main()
