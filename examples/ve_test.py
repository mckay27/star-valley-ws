from vedirect import VEDirect
import time

def print_callback(packet):
    print(packet)
    print()
    for i in packet:
        if i in VEDirect.values:
            print(VEDirect.values[i]["key"], end=": ")
        else:
            print(str(i), end=": ")
        
        if i == "ERR":
            print(VEDirect.error_codes[packet[i]], end=" ")
        elif i == "CS":
            print(VEDirect.device_state_map[packet[i]], end=" ")
        elif i == "MPPT":
            print(VEDirect.trackerModeDecode[packet[i]], end = " ")
        else:
            print(str(packet[i]), end=" ")


        if i in VEDirect.units:
            print(VEDirect.units[i])

    print()
    print("___________________________________________________________")
    print()

def print_callback_csv(packet):
    print(time.time(), end=", ")
    volts = packet.get("V", None)
    if volts is not None:
        volts = volts * .001
    else:
        volts = "N/A"
    print(volts, end=", ")
    i = packet.get("I", None)
    if i is not None:
        i = i * .001
    print(i, end=", ")
    panelv = packet.get("VPV", None)
    if panelv is not None:
        panelv = panelv * .001
    else:
        panelv = "N/A"
    print(panelv, end=", ")
    panelp = packet.get("PPV", None)
    if panelp == 0:
        paneli = 0
    elif panelp is not None:
        paneli = panelp / panelv
    else:
        paneli = "N/A"
    print(paneli)


ve = VEDirect("/dev/ttyAMA1", 60)

# Change print_callback_csv to print_callback for full data
ve.read_data_callback(print_callback_csv)
