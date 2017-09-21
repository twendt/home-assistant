import math

#Get state and brightness from A5:38:08 dim ack packet
def gateway_dim_state(packet):
    packet.parse_eep(0x38, 0x08, command=2)
    parsed = packet.parsed
    edim_val = parsed['EDIM']['raw_value']
    sw_val = parsed['SW']['raw_value']

    if sw_val == 1:
        brightness = math.floor(edim_val / 100.0 * 256.0)
        state = True
    else:
        state = False
        brightness = 0
    return state, brightness

#Get state from F6:02:02 switch ack packet
def rps_r1_binary_ack_state(packet):
    packet.parse_eep(0x02, 0x02)
    parsed = packet.parsed
    r1_val = parsed['R1']['raw_value']

    if r1_val == 3:
        state = True
    if r1_val == 2:
        state = False
    return state
