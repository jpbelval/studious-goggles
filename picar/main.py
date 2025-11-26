import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import json
from Ultrasonic_Avoidance import Ultrasonic_Avoidance
from Line_Follower import Line_Follower
from SunFounder_PiCar.picar import back_wheels, front_wheels
from SunFounder_PiCar import picar

# 0: Puissance
# 1: Angle

Ultra = Ultrasonic_Avoidance(17)
Line = Line_Follower()
bw = back_wheels.Back_Wheels(db='config')
fw = front_wheels.Front_Wheels(db='config')
fw.turning_max = 45

latest_message = None
processing_task = None

async def handle_client(websocket):
    loop = asyncio.get_running_loop()
    alive = asyncio.Event()
    alive.set()

    async def sender():
        while alive.is_set():
            try:
                distance = await loop.run_in_executor(None, Ultra.get_distance)
                #line_d  = await loop.run_in_executor(None, Line.read_digital)
                #line_a  = await loop.run_in_executor(None, Line.read_analog)
                line_r  = await loop.run_in_executor(None, Line.read_raw)

                data = {
                    "UltraValue": distance,
                    #"LineValue": line_d,
                    #"Analog": line_a,
                    "Raw": line_r
                }

                await websocket.send(json.dumps(data))
                await asyncio.sleep(0.0005)

            except ConnectionClosed:
                alive.clear()

    async def receiver():
        global latest_message, processing_task

        try:
            async for message in websocket:
                latest_message = message

                if processing_task is None or processing_task.done():
                    processing_task = asyncio.create_task(process_latest)

        except ConnectionClosed:
            pass
        finally:
            alive.clear()
            bw.speed = 0

    async def process_latest():
        global latest_message
        message = latest_message

        if message == latest_message:
            await update_car(message)

    async def update_car(message):
        print(message)
        engine = json.loads(message)
        forward_speed = int(engine["0"])
        angle = int(engine["1"])

        fw.turn(angle)

        if forward_speed < 0:
            bw.backward()
            bw.speed = -forward_speed
        else:
            bw.forward()
            bw.speed = forward_speed

    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())
    process_task = asyncio.create_task(process_latest())

    await asyncio.wait(
        [send_task, recv_task, process_task],
        return_when=asyncio.ALL_COMPLETED
    )

    for task in (send_task, recv_task, process_task):
        if not task.done():
            task.cancel()

    alive.clear()


async def main():
    picar.setup()
    async with serve(handle_client, None, 8765):
        print("Serveur WebSocket démarré sur le port 8765")
        await asyncio.Future()

asyncio.run(main())
