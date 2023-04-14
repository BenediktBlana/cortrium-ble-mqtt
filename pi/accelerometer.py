# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Connect to an "eval()" service over BLE UART.
import time
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
import paho.mqtt.client as mqtt

ble = BLERadio()

uart_connection = None

mFirstBatchAfterConnection = True

C1_Value = 0
C2_Value = 0
C3_Value = 0


def convert_16bit_sign_value(value):
    # Check if the value is negative
    if value & 0x8000:
        # Convert the value to a negative 16-bit integer
        value = -(0x10000 - value)
    return value


def decode_c(Line):
    Length = Line[0]
    if Length < 57:
        return print("Telegram is too short")
    else:
        print("Telegram length: ", Length)
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

    Acc_X = convert_16bit_sign_value(
        (((Line[index] << 4) & 0xFF0) | ((Line[index + 1] >> 4) & 0x0F)) << 4
    )  # // 5 6 // 0xFFF0
    Acc_Y = convert_16bit_sign_value(
        (((Line[index + 1] & 0x0F) << 8) | (Line[index + 2] & 0xFF)) << 4
    )  # // 6 7 // 0xFFF0
    Acc_Z = convert_16bit_sign_value(
        (((Line[index + 3] << 4) & 0xFF0) | ((Line[index + 4] >> 4) & 0x0F)) << 4
    )  # // 8 9 // 0xFFF0

    if Acc_X and Acc_Y and Acc_Z:
        print(f"Accelererometer X: {Acc_X/16} Y: {Acc_Y/16} Z: {Acc_Z/16}")

    topic = "cortrium/accelerometer"
    message = f'{{ "x": "{Acc_X/16}", "y": {Acc_Y/16}, "y": {Acc_Z/16} }}'
    # client.publish(topic, message)

    # index += 4
    # Events = Line[index] & 0x0F
    # index += 1
    # Vbat = 0
    # Button = 0
    # LOD_Active = 0x00


# # set up MQTT
# client = mqtt.Client()
# client.connect("localhost", 1883)

while True:
    if not uart_connection:
        print("Trying to connect...")
        for adv in ble.start_scan(ProvideServicesAdvertisement):
            if adv.complete_name == "C3050319":
                print("RSSI: ", adv.rssi)
                print("RSSI: ", adv.address)

            if UARTService in adv.services:
                uart_connection = ble.connect(adv)
                print("Connected")
                break
        ble.stop_scan()

    if uart_connection and uart_connection.connected:
        uart_service = uart_connection[UARTService]
        while uart_connection.connected:
            data = uart_service.readline()
            if data is not None:
                decode_c(uart_service.readline())
                time.sleep(1)
        # print('read: ', len(uart_service.read()))
        # print('readline: ', len(uart_service.readline()))
        # if (len(uart_service.readline()) >= 57):
        #     decode_c(uart_service.readline())
        # # Returns b'' if nothing was read.
        # if (uart_service and uart_service.readline()):
        #     # First byte contains the length of the telegram
        #     decode_c(uart_service.readline())

    ble.stop_scan()
