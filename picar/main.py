import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosed

from Ultrasonic_Avoidance import Ultrasonic_Avoidance
from Line_Follower import Line_Follower
from SunFounder_PiCar.picar import back_wheels

async def handle_client(websocket):
    Ultra = Ultrasonic_Avoidance(17)
    Line = Line_Follower()
    bw = back_wheels.Back_Wheels(db='config')
    forward_speed = 90
    bw.forward()
    bw.speed = forward_speed
    async def sender():
        while True:
            try:
                data = {
                    "UltraValue": Ultra.get_distance(),
                    "LineValue": Line.read_digital()
                }
                await websocket.send(str(data))
                await asyncio.sleep(0.05)
            except ConnectionClosed:
                break

    async def receiver():
        async for message in websocket:
            print("Commande reçue :", message)

            pass

    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())

    done, pending = await asyncio.wait(
        [send_task, recv_task],
        return_when=asyncio.FIRST_EXCEPTION
    )

    for task in pending:
        task.cancel()

async def main():
    picar.setup()
    async with serve(handle_client, None, 8765):
        print("Serveur WebSocket démarré sur le port 8765")
        await asyncio.Future()

asyncio.run(main())
