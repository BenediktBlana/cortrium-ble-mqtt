"""Example of how to create a Central device/GATT Client"""
from enum import IntEnum
import struct

from bluezero import adapter
from bluezero import central

# Documentation can be found on Bluetooth.com
# https://www.bluetooth.com/specifications/specs/heart-rate-service-1-0/

# There are also published xml specifications for possible values
# For the Service:
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.service.heart_rate.xml

# For the Characteristics:
# Heart Rate Measurement
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.heart_rate_measurement.xml
# Body Sensor Location
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.body_sensor_location.xml
# Heart Rate Control Point
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.heart_rate_control_point.xml

# constants
UART_SERVICE = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_CHARACTERISTIC = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
TX_CHARACTERISTIC = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'


class HeartRateMeasurementFlags(IntEnum):
    HEART_RATE_VALUE_FORMAT_UINT16 = 0b00000001
    SENSOR_CONTACT_DETECTED = 0b00000010
    SENSOR_CONTACT_SUPPORTED = 0b00000100
    ENERGY_EXPENDED_PRESENT = 0b00001000
    RR_INTERVALS_PRESENT = 0b00010000


def convert_24bit_sign_value(value):
    if value & 0x800000:
        value = -(0x1000000 - value)
    return value


def convert_16bit_sign_value(value):
    if value & 0x8000:
        value = -(0x10000 - value)
    return value


def convert_8bit_sign_value(value):
    if value & 0x80:
        value = -(0x100 - value)
    return value


def decode_c(Line):

    C1_Value = 0
    C2_Value = 0
    C3_Value = 0

    Length = Line[0]
    index = 0

    # Decodes Part1 of the telegram
    len = Line[index]
    index += 1
    New_ID = Line[index]
    index += 1
    Index_Counter = Line[index]
    index += 1
    Samples = Line[index]
    index += 1

    Acc_X = convert_16bit_sign_value((((Line[index] << 4) & 0xFF0) | (
        (Line[index + 1] >> 4) & 0x0F)) << 4)  # // 5 6 // 0xFFF0
    Acc_Y = convert_16bit_sign_value(
        (((Line[index + 1] & 0x0F) << 8) | (Line[index + 2] & 0xFF)) << 4)  # // 6 7 // 0xFFF0
    Acc_Z = convert_16bit_sign_value(
        (((Line[index + 3] << 4) & 0xFF0) | ((Line[index + 4] >> 4) & 0x0F)) << 4)  # // 8 9 // 0xFFF0

    if (Acc_X and Acc_Y and Acc_Z):
        print(f'Accelererometer X: {Acc_X/16} Y: {Acc_Y/16} Z: {Acc_Z/16}')

    index += 4
    Events = Line[index] & 0x0F
    index += 1

    if Events != 0x00:  # Read event bytes
        # index = index + 2/4/6/8
        if (Events & 0x01) == 0x01:  # Vbat event
            value = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)  # 10 11
            index += 2
            fVbat = float(value) * 0.6 * 3 * 3 / 1024
            # print("VBat fVbat = {}".format(fVbat))

        if (Events & 0x02) == 0x02:  # LOD event
            value = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)  # 10 11
            index += 2
            # print("LOD_Active = {}".format(value))

        if (Events & 0x04) == 0x04:  # Button event
            Button = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)  # 10 11
            index += 2
            # print("Button = {}".format(Button))

    C1_Compression = 0
    C2_Compression = 0
    C3_Compression = 0

    # Number of samples determines how many bytes are used for compression mask
    if Samples > 12:
        C1_Compression = ((Line[index] << 24) & 0xFF000000) | ((Line[index + 1] << 16) & 0x00FF0000) | (
            (Line[index + 2] << 8) & 0x0000FF00) | (Line[index + 3] & 0x000000FF)  # 10 11 12 13
        C2_Compression = ((Line[index + 4] << 24) & 0xFF000000) | ((Line[index + 5] << 16) & 0x00FF0000) | (
            (Line[index + 6] << 8) & 0x0000FF00) | (Line[index + 7] & 0x000000FF)  # 14 15 16 17
        C3_Compression = ((Line[index + 8] << 24) & 0xFF000000) | ((Line[index + 9] << 16) & 0x00FF0000) | (
            (Line[index + 10] << 8) & 0x0000FF00) | (Line[index + 11] & 0x000000FF)  # 18 19 20 21
        index += 12
    elif Samples > 8:
        C1_Compression = ((Line[index] << 16) & 0xFF0000) | (
            (Line[index + 1] << 8) & 0x00FF00) | (Line[index + 2] & 0x0000FF)  # 10 11 12
        C2_Compression = ((Line[index + 3] << 16) & 0xFF0000) | (
            (Line[index + 4] << 8) & 0x00FF00) | (Line[index + 5] & 0x0000FF)  # 13 14 15
        C3_Compression = ((Line[index + 6] << 16) & 0xFF0000) | (
            (Line[index + 7] << 8) & 0x00FF00) | (Line[index + 8] & 0x0000FF)  # 16 17 18
        index += 9
    else:
        C1_Compression = ((Line[index] << 8) & 0xFF00) | (
            Line[index + 1] & 0x00FF)  # 10 11
        C2_Compression = ((Line[index + 2] << 8) &
                          0xFF00) | (Line[index + 3] & 0x00FF)  # 12 13
        C3_Compression = ((Line[index + 4] << 8) &
                          0xFF00) | (Line[index + 5] & 0x00FF)  # 14 15
        index += 6

    C1_Diff = 0
    C2_Diff = 0
    C3_Diff = 0

    tmp_buf = 0
    bitmast = 0

    for i in range(Samples - 1, -1, -1):
        bitmask = (C1_Compression >> (i * 2)) & 0x03

        if bitmask == 2:
            tmp_buf = ((Line[index] << 16) & 0xFF0000) | (
                (Line[index + 1] << 8) & 0x00FF00) | ((Line[index + 2]) & 0x0000FF)
            C1_Diff = convert_24bit_sign_value(tmp_buf)
            index += 3
        elif bitmask == 1:
            tmp_buf = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)
            C1_Diff = convert_16bit_sign_value(tmp_buf)
            index += 2
        else:
            tmp_buf = (Line[index] & 0x00FF)
            C1_Diff = convert_8bit_sign_value(tmp_buf)
            index += 1

        bitmask = (C2_Compression >> (i * 2)) & 0x03

        if bitmask == 2:
            tmp_buf = ((Line[index] << 16) & 0xFF0000) | (
                (Line[index + 1] << 8) & 0x00FF00) | ((Line[index + 2]) & 0x0000FF)
            C2_Diff = convert_24bit_sign_value(tmp_buf)
            index += 3
        elif bitmask == 1:
            tmp_buf = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)
            C2_Diff = convert_16bit_sign_value(tmp_buf)
            index += 2
        else:
            tmp_buf = (Line[index] & 0x00FF)
            C2_Diff = convert_8bit_sign_value(tmp_buf)
            index += 1

        bitmask = (C3_Compression >> (i * 2)) & 0x03

        if bitmask == 2:
            tmp_buf = ((Line[index] << 16) & 0xFF0000) | (
                (Line[index + 1] << 8) & 0x00FF00) | ((Line[index + 2]) & 0x0000FF)
            C3_Diff = convert_24bit_sign_value(tmp_buf)
            index += 3
        elif bitmask == 1:
            tmp_buf = ((Line[index] << 8) & 0xFF00) | (
                Line[index + 1] & 0x00FF)
            C3_Diff = convert_16bit_sign_value(tmp_buf)
            index += 2
        else:
            tmp_buf = (Line[index] & 0x00FF)
            C3_Diff = convert_8bit_sign_value(tmp_buf)
            index += 1

        if index >= Length:
            print("decode error : ( index > Length ) : " +
                  str(index) + " >= " + str(Length))

        C1_Value += C1_Diff
        C2_Value += C2_Diff
        C3_Value += C3_Diff

        print(C1_Value, C2_Value, C3_Value)

        iECGindex = Samples - 1 - i
        # decoded_iECG1[iECGindex] = C1_Value
        # decoded_iECG2[iECGindex] = C2_Value
        # decoded_iECG3[iECGindex] = C3_Value


def scan_for_heartrate_monitors(
        adapter_address=None,
        hrm_address=None,
        timeout=5.0):
    """
    Called to scan for BLE devices advertising the Heartrate Service UUID
    If there are multiple adapters on your system, this will scan using
    all dongles unless an adapter is specfied through its MAC address
    :param adapter_address: limit scanning to this adapter MAC address
    :param hrm_address: scan for a specific peripheral MAC address
    :param timeout: how long to search for devices in seconds
    :return: generator of Devices that match the search parameters
    """
    # If there are multiple adapters on your system, this will scan using
    # all dongles unless an adapter is specified through its MAC address
    for dongle in adapter.Adapter.available():
        # Filter dongles by adapter_address if specified
        if adapter_address and adapter_address.upper() != dongle.address():
            continue

        # Actually listen to nearby advertisements for timeout seconds
        dongle.nearby_discovery(timeout=timeout)

        # Iterate through discovered devices
        for dev in central.Central.available(dongle.address):
            # Filter devices if we specified a HRM address
            if hrm_address and hrm_address == dev.address:
                yield dev

            # Otherwise, return devices that advertised the HRM Service UUID
            if UART_SERVICE.lower() in dev.uuids:
                yield dev


def on_new_heart_rate_measurement(iface, changed_props, invalidated_props):
    """
    Callback used to receive notification events from the device.
    :param iface: dbus advanced data
    :param changed_props: updated properties for this event, contains Value
    :param invalidated_props: dvus advanced data
    """
    value = changed_props.get('Value', None)
    if not value:
        return
    # decode bytearray and red accelerometer values
    decode_c(value)

    # print(f"Total Exercise Calories Burned: {energy_expended / 4.184}")


def connect_and_run(dev=None, device_address=None):
    """
    Main function intneded to show usage of central.Central
    :param dev: Device to connect to if scan was performed
    :param device_address: instead, connect to a specific MAC address
    """
    # Create Interface to Central
    if dev:
        monitor = central.Central(
            adapter_addr=dev.adapter,
            device_addr=dev.address)
    else:
        monitor = central.Central(device_addr=device_address)

    # Characteristics that we're interested must be added to the Central
    # before we connect so they automatically resolve BLE properties
    # Heart Rate Measurement - notify
    tx_char = monitor.add_characteristic(UART_SERVICE, TX_CHARACTERISTIC)

    # Now Connect to the Device
    if dev:
        print("Connecting to " + dev.alias)
    else:
        print("Connecting to " + device_address)

    monitor.connect()

    # Check if Connected Successfully
    if not monitor.connected:
        print("Didn't connect to device!")
        return

    # Enable heart rate notifications
    tx_char.start_notify()
    tx_char.add_characteristic_cb(on_new_heart_rate_measurement)

    try:
        # Startup in async mode to enable notify, etc
        monitor.run()
    except KeyboardInterrupt:
        print("Disconnecting")

    tx_char.stop_notify()
    monitor.disconnect()


if __name__ == '__main__':
    # Discovery nearby heart rate monitors
    devices = scan_for_heartrate_monitors()
    for hrm in devices:
        print("Heart Rate Measurement Device Found!")

        # Connect to first available heartrate monitor
        connect_and_run(hrm)

        # Only demo the first device found
        break
