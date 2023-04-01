import Adafruit_BluefruitLE

# Get the BLE connection object
ble = Adafruit_BluefruitLE.get_provider()
ble.initialize()
adapter = ble.get_default_adapter()
adapter.power_on()
print('Searching for devices...')
try:
    adapter.start_scan()
    device = ble.find_device(name='C3050319')
    if device is None:
        raise Exception('Could not find device!')
    device.connect()
    rssi = device.get_connected_device_rssi()
    print('RSSI:', rssi)
finally:
    adapter.stop_scan()
    device.disconnect()
