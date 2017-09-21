def get_hex_list_from_str(hexstr):
    return [get_int_from_str(part_str) for part_str in hexstr.split(':')]

def get_int_from_str(hexstr):
    hex_int = int("0x{}".format(hexstr), 16)
    return hex_int
