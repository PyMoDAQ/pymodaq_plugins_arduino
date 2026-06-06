"""
Test minimal - ESP32 PWM sur GPIO17 (D8) via telemetrix-aio-esp32
Lancer avec : python test_esp32_pwm.py

Ce script teste directement sans PyMoDAQ pour isoler le problème hardware.
"""

import asyncio
import time

from telemetrix_aio_esp32 import telemetrix_aio_esp32

ESP32_IP   = "172.17.50.238"
ESP32_PORT = 31336
FAN_PIN    = 17   # D8 sur Arduino Nano ESP32
FAN_CH     = 0    # canal PWM (0-15, unique par pin)


async def main():
    print(f"Connexion a {ESP32_IP}:{ESP32_PORT} ...")

    board = telemetrix_aio_esp32.TelemetrixAioEsp32(
        transport_is_wifi=True,
        transport_address=ESP32_IP,
        ip_port=ESP32_PORT,
        autostart=False,
        shutdown_on_exception=True,
        restart_on_shutdown=False,
    )

    await board.start_aio()
    print("Connecte. Firmware OK.")

    # Attente stabilisation
    await asyncio.sleep(1)

    # --- Configurer le pin en PWM ---
    print(f"Configuration GPIO{FAN_PIN} en analog output (PWM), canal {FAN_CH} ...")
    await board.set_pin_mode_analog_output(
        FAN_PIN,
        channel=FAN_CH,
        frequency=5000.0,
        resolution=8,
    )
    await asyncio.sleep(0.5)

    # --- Test 1 : valeur maximale (255) ---
    print("PWM = 255 (100%) pendant 5 secondes ...")
    await board.analog_write(FAN_CH, 255)
    await asyncio.sleep(5)

    # --- Test 2 : valeur moyenne (128) ---
    print("PWM = 128 (50%) pendant 5 secondes ...")
    await board.analog_write(FAN_CH, 128)
    await asyncio.sleep(5)

    # --- Test 3 : extinction ---
    print("PWM = 0 (off) ...")
    await board.analog_write(FAN_CH, 0)
    await asyncio.sleep(1)

    print("Shutdown.")
    await board.shutdown()


if __name__ == "__main__":
    asyncio.run(main())