import time
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()

nus_advertisement = None
while nus_advertisement is None:
    for adv in ble.start_scan(ProvideServicesAdvertisement):
        if UARTService in adv.services:
            nus_advertisement = adv
            break
    ble.stop_scan()
    time.sleep(0.1)

nus_device = ble.connect(nus_advertisement)
uart_service = nus_device[UARTService]


uart_service.start_notify(uart_service.rx_characteristic)

while True:
    if uart_service.in_waiting:
        received_bytes = uart_service.read(uart_service.in_waiting)
        print(received_bytes.decode("utf-8"))
    time.sleep(0.1)
