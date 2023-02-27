# C3050319
# d3:33:51:84:40:dc
import gatt
import json
import helper

GENERIC_ATTRIBUTES_SERVICE = '00001801-0000-1000-8000-00805f9b34fb'
BLE_CHARACTERISTIC_UUID_Rx = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
BLE_CHARACTERISTIC_UUID_Tx = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
BLE_SERVICE_UUID_C3TESTER = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'

manager = gatt.DeviceManager(adapter_name='hci0')
outputChar = None


def write_data_to_char(characteristic, bytearray_data):
    # if(bytearray_data.length > 20):
    #     raise ValueError("Byte array is too big")

    if (characteristic is not None):
        characteristic.write_value(bytearray(bytearray_data))


class AnyDeviceManager(gatt.DeviceManager):
    def device_discovered(self, device):
        print("Discovered [%s] %s" % (device.mac_address, device.alias()))


class AnyDevice(gatt.Device):
    def connect_succeeded(self):
        super().connect_succeeded()
        print("[%s] Connected" % (self.mac_address))

    def connect_failed(self, error):
        super().connect_failed(error)
        print("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def disconnect_succeeded(self):
        super().disconnect_succeeded()
        print("[%s] Disconnected" % (self.mac_address))

    def services_resolved(self):
        super().services_resolved()

        print("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            print("[%s]  Service [%s]" % (self.mac_address, service.uuid))
            for characteristic in service.characteristics:
                print("[%s]    Characteristic [%s]" %
                      (self.mac_address, characteristic.uuid))
                if (characteristic.uuid == BLE_CHARACTERISTIC_UUID_Tx):
                    outputChar = characteristic
                    characteristic.enable_notifications()
                    print('enabling notifications...')

    def characteristic_value_updated(self, characteristic, value):
        # msg = bytearray(value.decode('utf-8'))
        print(value['0x7F'])
        # str_decoded = value.decode()
        # print(type(str_decoded))
        # print(eval(str(value)).decode('utf-8'))
        print('\n')

    def characteristic_enable_notifications_succeeded():
        super().characteristic_enable_notifications_succeeded()


device = AnyDevice(mac_address='d3:33:51:84:40:dc', manager=manager)

print("Connecting...")

device.connect()

manager.run()
