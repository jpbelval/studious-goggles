import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import json
from Ultrasonic_Avoidance import Ultrasonic_Avoidance
from Line_Follower import Line_Follower
from SunFounder_PiCar.picar import back_wheels, front_wheels
from SunFounder_PiCar import picar
import time

# 0: Puissance
# 1: Angle
THEORIC_MIDDLE_ANGLE = 100

Ultra = Ultrasonic_Avoidance(17)
Line = Line_Follower()
bw = back_wheels.Back_Wheels(db='config')
fw = front_wheels.Front_Wheels(db='config')
fw.turning_max = 45

LINE_ULTRA_TICKRATE = 30


latest_message = None
processing_task = None

def drive_differentiel(turn_angle, speed):

    turn_sensitivity = 0.3 # a ajuster

    turn_factor = (turn_angle - THEORIC_MIDDLE_ANGLE) / fw.turning_max
    if turn_factor > 1:
        turn_factor = 1
    elif turn_factor < -1:
        turn_factor = -1

    if speed < 0:
        bw.backward()
        speed = -speed
    else:
        bw.forward()

    if turn_factor > 0: # Gauche
        bw.left_wheel.speed = int(speed * (1 - (abs(turn_factor) * turn_sensitivity)))
        bw.right_wheel.speed = int(speed)
    elif turn_factor < 0:
        bw.left_wheel.speed = int(speed)
        bw.right_wheel.speed = int(speed * (1 - (abs(turn_factor) * turn_sensitivity)))
    else:
        bw.left_wheel.speed = int(speed)
        bw.right_wheel.speed = int(speed)
    
    
async def handle_client(websocket):
    loop = asyncio.get_running_loop()
    alive = asyncio.Event()
    alive.set()

    async def sender():
        while alive.is_set():
            try:
                start_time = time.time()

                distance = await loop.run_in_executor(None, Ultra.get_distance)
                line_r  = await loop.run_in_executor(None, Line.read_raw)

                data = {
                    "UltraValue": distance,
                    "Raw": line_r
                }

                await websocket.send(json.dumps(data))

                elapsed = time.time() - start_time
                sleep_time = (1/LINE_ULTRA_TICKRATE) - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            except ConnectionClosed:
                alive.clear()

    async def receiver():
        try:
            async for message in websocket:
                engine = json.loads(message)
                forward_speed = int(engine["0"])
                angle = int(engine["1"])

                fw.turn(angle)

                drive_differentiel(angle, forward_speed)

        except ConnectionClosed:
            pass
        finally:
            alive.clear()
            bw.speed = 0

    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())

    await asyncio.wait(
        [send_task, recv_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in (send_task, recv_task):
        if not task.done():
            task.cancel()

    alive.clear()


async def main():
    picar.setup()
    async with serve(handle_client, None, 8765):
        print("Serveur WebSocket démarré sur le port 8765")
        await asyncio.Future()

asyncio.run(main())