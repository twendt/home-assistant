import math
from enocean.protocol.constants import RORG, PACKET
from enocean.protocol.packet import RadioPacket, Packet
from homeassistant.components.enocean.util import  get_hex_list_from_str

#Generate A5:38:08 dim command
def gateway_dim_command(sender_id, destination_id, brightness):
    new_state = 0 if brightness == 0 else 1
    sender_id_arr = get_hex_list_from_str(sender_id)
    destination_id_arr = get_hex_list_from_str(destination_id)
    try:
        pack = RadioPacket.create(
            rorg=RORG.BS4,
            rorg_func=0x38,
            rorg_type=0x08,
            sender=sender_id_arr,
            destination=destination_id_arr,
            command=2,
            EDIM=brightness,
            RMP=1,
            LRNB=1,
            EDIMR=0,
            STR=0,
            SW=new_state)
    except:
        return None
    return pack

#Generate A5:38:08 dim on command
def gateway_dim_on(sender_id, destination_id, brightness):
    brightness = math.floor(brightness / 256.0 * 100.0)
    pack = gateway_dim_command(sender_id, destination_id, brightness)
    return pack

#Generate A5:38:08 dim off command
def gateway_dim_off(sender_id, destination_id):
    pack = gateway_dim_command(sender_id, destination_id, 0)
    return pack

#Generate A5:38:08 switch command
def gateway_switch_command(sender_id, destination_id, new_state):
    sender_id_arr = get_hex_list_from_str(sender_id)
    destination_id_arr = get_hex_list_from_str(destination_id)
    try:
        pack = RadioPacket.create(
            rorg=RORG.BS4,
            rorg_func=0x38,
            rorg_type=0x08,
            sender=sender_id_arr,
            destination=destination_id_arr,
            command=1,
            TIM=0,
            LRNB=1,
            LCK=0,
            DEL=0,
            SW=new_state)
    except:
        return None
    return pack

#Generate A5:38:08 switch on command
def gateway_switch_on(sender_id, destination_id):
    pack = gateway_switch_command(sender_id, destination_id, 1)
    return pack

#Generate A5:38:08 switch off command
def gateway_switch_off(sender_id, destination_id):
    pack = gateway_switch_command(sender_id, destination_id, 0)
    return pack
