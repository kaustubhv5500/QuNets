from binary_string import binary as secret_message
from qunetsim import Host, Network, Logger, Qubit
import random

Logger.DISABLED = True
IS_EPR = '1'
IS_DATA = '0'
DATA_FRAME = 8

# The dataframe length should divide the length of the secret string
assert len(secret_message) % DATA_FRAME == 0

EPR_FRAME = 4
cur_location = 0
p = 0.75

def dense_encode(q: Qubit, bits: str):
    """
    Assumptions: - Qubit *q* is entangled with another qubit q' which resides at receiver
                 - Think of dense_encode as an optical device at the sender side, where each
                  qubit has to pass through the optical device

    Parameters
    ----------
    bits : str
        A two-bit string

    Returns
    -------
    Qubit
        The encoded qubit
    """

    # Depending on the 2 bit incoming message, determine the encoding
    # on qubit *q*.

    # TODO: Apply the superdense coding logic to qubit *q*
    # Based on the bits, encode the qubit using gates
    if bits == '00':
        q.I()
    elif bits == '01':
        q.X()
    elif bits == '10':
        q.Z()
    elif bits == '11':
        q.X()
        q.Z()
    return q


def dense_decode(stored_epr_half: Qubit, received_qubit: Qubit) -> str:
    """
    Decode the two bit message encoded in *stored_epr_half* and *received_qubit*.

    Parameters
    ----------
    stored_epr_half : Qubit
        One half of the EPR pair for superdense coding
    received_qubit : Qubit
        One half of the EPR pair for superdense coding, received from sender

    Returns
    -------
    str
        Two bit message
    """
    meas = '00'

    # TODO: Apply the superdense decoding scheme to the two input qubits
    #       and return a string of the binary output
    stored_epr_half.cnot(received_qubit)
    stored_epr_half.H()

    q1 = stored_epr_half.measure()
    q2 = received_qubit.measure()
    meas = str(q1) + str(q2)
    return meas


def encode_qubit(q: Qubit, bit: str) -> Qubit:
    """Encode the qubit *q* with bit *bit*.

    Parameters
    ----------
    q : Qubit
        The qubit to encode
    bit : str
        The bit to encode

    Returns
    -------
    Qubit
        The encoded qubit

    Raises
    ------
    Exception
        Input must be 0 or 1. Raise an exception otherwise.
    """

    # TODO: Based on the input bit, perform the respective encoding on
    #       the input qubit
    if bit == '0':
        pass
    elif bit == '1':
        q.X()
    else:
        raise Exception('Input must be either 0 or 1')
    
    return q


def decode_qubit(q: Qubit) -> str:
    """Summary

    Parameters
    ----------
    q : Qubit
        The qubit to decode

    Returns
    -------
    str
        One bit with the qubit measurement result.
    """
    meas = q.measure()
    return str(meas)


def get_next_message() -> str:
    """
    With some probability, retreive *DATA_FRAME* bits of the message to transmit.
    When there are no more bits to transmit False is returned.

    Returns
    -------
    str
        A 1 or 2 bit message with probability *p*, -1 with *1 - p*, or False.
    """
    global cur_location
    if len(secret_message) == cur_location:
        return False

    should_send = random.random() <= p
    if should_send:
        msg = secret_message[cur_location: cur_location + DATA_FRAME]
        cur_location += DATA_FRAME
        return msg
    return -1


def decode_secret_message(binary_message: str):
    """
    Decode the ASCII values of *binary_message*.

    Parameters
    ----------
    binary_message : str
        The binary string to decode.
    """
    global p
    binary_int = int(binary_message, 2)
    byte_number = binary_int.bit_length() + 7 // 8
    binary_array = binary_int.to_bytes(byte_number, "big")
    ascii_text = binary_array.decode()
    print(f'Secret message:\n{ascii_text}')


def sender_protocol(host, receiver):
    cur_message = get_next_message()
    while cur_message:
        leading_qubit = Qubit(host)

        # Hint: Refer to the constants above for how to transmit the frames
        # Hint: Use the `await_ack=True` flag when sending qubits to keep
        #       the sender and receiver in sync
        if cur_message == -1:
            # TODO: Fill in the logic for when there is no message to send
            # Hint: You can use host.add_epr(receiver, qubit) to store EPR halfs
            #       after generating them
            leading_qubit.X()
            q_id, ack_arrived = host.send_qubit(receiver, leading_qubit, await_ack = True)
            for i in range(EPR_FRAME):
                qubit = Qubit(host)
                target = Qubit(host)
                qubit.H()
                qubit.cnot(target=target)
                host.add_epr(receiver, qubit)
                host.send_qubit(receiver, target, await_ack=True)

        else:
            leading_qubit.I()
            q_id, ack_arrived = host.send_qubit(receiver, leading_qubit, await_ack = True)
            # TODO: Fill in the logic for when there is a message to send
            # Hint: You can use host.shares_epr(receiver) to determine how the
            #       message should be encoded.
            # Hint: Use the encoding methods from above.
            if host.shares_epr(receiver):
                for i in range(0, len(cur_message), 2):
                    epr = host.get_epr(receiver)
                    encoded_qubit = dense_encode(epr, str(cur_message[i] + cur_message[i+1]))
                    q_id, ack_arrived = host.send_qubit(receiver, encoded_qubit, await_ack=True)
            else:
                for bit in cur_message:
                    qubit = Qubit(host)
                    encoded_qubit = encode_qubit(qubit, bit)
                    q_id, ack_arrived = host.send_qubit(receiver, encoded_qubit, await_ack = True)
        cur_message = get_next_message()


def receiver_protocol(host, sender):
    binary_message = ''
    while True:
        received_qubit = host.get_data_qubit(sender, wait=10)
        if received_qubit is None:
            break
        # TODO: Retreive the header bit
        header_bit = received_qubit.measure()
        if str(header_bit) == IS_EPR:
            # TODO: Fill in the logic for what to do when the header qubit
            #       indicates EPR qubits arriving. Hint: EPR_FRAME defines
            #       how many EPR pair halves will arrive.
            for i in range(EPR_FRAME):
                shared_epr = host.get_qubit(sender, wait = 11)
                host.add_epr(sender, shared_epr)
                
        else:
            # TODO: Fill in the logic for what to do when the header qubit
            #       indicates data is arriving.
            # Hint: You can use host.shares_epr(sender) to determine how the
            #       message should be decoded
            if host.shares_epr(sender):
                for i in range(EPR_FRAME):
                    shared_epr = host.get_epr(sender)
                    qubit = host.get_qubit(sender, wait = 1)
                    decoded = dense_decode(shared_epr, qubit)
                    binary_message += decoded
            else:
                for i in range(DATA_FRAME):
                    qubit = host.get_qubit(sender, wait = 10)
                    decoded = decode_qubit(qubit)
                    binary_message += decoded
    decode_secret_message(binary_message)



def main():
    network = Network.get_instance()
    network.start()

    host_A = Host('A')
    host_A.add_connection('B')
    host_A.start()
    host_B = Host('B')
    host_B.add_connection('A')
    host_B.start()

    network.add_hosts([host_A, host_B])

    t1 = host_A.run_protocol(sender_protocol, ('B',))
    t2 = host_B.run_protocol(receiver_protocol, ('A',), blocking=True)

    network.stop(True)

if __name__ == '__main__':
    main()
