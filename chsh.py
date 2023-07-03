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

Logger.DISABLED = False

## CONSTANTS
STRATEGY_A = [0, np.pi/4]
STRATEGY_B = [np.pi/8, -np.pi/8]

def get_unitary(angle):
    return np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])

class Referee():
    def __init__(self):
        self.host = Host('Referee')
        self.question = None
        self.players = []
        self.proto = None

    def register_player(self, player):
        self.players.append(player)

    def generate_questions(self):
        self.questions = [random.randint(0,1) for p in self.players]

    def evaluate_answers(self, answers):
        
        q = 1
        for questions in self.question:
            q *= questions
        
        ans = 0
        for answer in answers:
            a = a ^ answer
        
        if q == a:
            return True
        else:
            return False

    def protocol(self):
        while True:
            self.generate_questions()
            for i, player in enumerate(self.players):
                self.host.send_classical(player.host.host_id, self.questions[i])

            answers = []
            strategies = []
            for i, player in enumerate(self.players):
                msg = player.host.get_classical(player.host.host_id, wait = -1)[-1]
                msg = msg.content.split(",")
                answers.append(int(msg[0]))
                strategies.append(msg[1])
            res = self.evaluate_answers(answers)
            print(answers)

    def run(self):
        self.proto = Thread(target=self.protocol)
        self.proto.start()

class Player():
    def __init__(self, strategy, name):
        self.host = Host(name)
        self.strategy = strategy
        self.referee = None
        self.epr_gen = None
        self.qubit = None
        self.proto = None

    def register_referee(self, referee):
        self.referee = referee
    
    def register_epr(self, epr_gen):
        self.epr_gen = epr_gen

    def request_epr(self):
        self.host.send_classical(self.epr_gen.host.host_id, "0")
        self.host.get_data_qubit(self.epr_gen.host.host_id, wait = 1)
        if self.qubit is None:
            return False
        else:
            return True


    def quantum_strategy(self, question):
        if question:
            self.qubit.custom_gate(get_unitary(self.strategy[1]))
        else:
            self.qubit.custom_gate(get_unitary(self.strategy[0]))
        
        return self.qubit.measure()

    def run(self):
        self.proto = Thread(target=self.protocol)
        self.proto.start()

    def protocol(self):
        while True:
            question = self.host.get_classical(self.referee.host.host_id, wait=-1)[-1]
            question = int(question.content)
            resp = self.request_epr()

            if resp is None:
                ans = 1
                strategy = 'C'
            else:
                ans = 1
                strategy = 'Q'

            self.qubit = None
            self.host.send_classical(self.referee.host.host_id, str(ans) + ',' + strategy)

class EPR_GEN():
    def __init__(self):
        self.host = Host('EPR_GEN')
        self.players = []
        self.proto = None

    def protocol(self):
        while True:
            for p in self.players:
                self.host.get_classical(p.host.host_id, wait=-1)

    def distribute_epr_pairs(self):
        qubits = [Qubit(self.host) for p in self.players]
        qubits[0].H()
        for q in qubits[1:]:
            qubits[0].cnot(q)
        
        for i, player in enumerate(self.players):
            self.host.send_qubit(player, qubits[i])


    def run(self):
        self.proto = Thread(target=self.protocol)
        self.proto.start()
    
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
    epr.host.add_connection(alice.host.host_id)
    epr.host.add_connection(bob.host.host_id)
    alice.host.add_connection(epr.host.host_id)
    bob.host.add_connection(epr.host.host_id)

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
    ref.register_player(alice)
    ref.register_player(bob)

    alice.register_referee(ref)
    bob.register_referee(ref)

    alice.register_epr(epr)
    bob.register_epr(epr)

    epr.register_player(alice)
    epr.register_player(bob)

    alice.run()
    bob.run()
    epr.run()
    ref.run()

    for hosts in [alice, bob, epr, ref]:
        hosts.proto.join()

if __name__ == "__main__":
    main()
