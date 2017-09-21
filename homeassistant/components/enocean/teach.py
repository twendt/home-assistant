from enocean.protocol.constants import RORG, PACKET
from enocean.protocol.packet import RadioPacket, Packet
from homeassistant.components.enocean.util import  get_hex_list_from_str

def generate_eltako_38_teachin(sender_id, destination_id):
    sender_id_arr = get_hex_list_from_str(sender_id)
    destination_id_arr = get_hex_list_from_str(destination_id)
    #Create Eltako Teachin Telegram E0:40:0D:80
    pack = Packet(PACKET.RADIO)
    pack.rorg = RORG.BS4
    pack.data = [pack.rorg]
    pack.data.extend([224, 64, 13, 128])
    pack.data.extend(sender_id_arr)
    pack.data.extend([0])
    pack.optional = [3] + destination_id_arr + [0xFF] + [0]
    return pack
