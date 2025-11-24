import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

import Ultrasonic_Avoidance
import Line_Follower

async def handle_client(websocket):
    async def sender():
        Ultra = Ultrasonic_Avoidance(17)
        Line = Line_Follower()
        while True:
            # Code des capteurs
            data = {"UltraValue": Ultra.get_distance(),
                    "LineValue": Line.read_analog()}
            await websocket.send(str(data))
            await asyncio.sleep(0.5)  # fréquence d’envoi

    async def receiver():
        async for message in websocket:
            # commandes moteurs
            i = 0

    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())

    done, pending = await asyncio.wait(
        [send_task, recv_task],
        return_when=asyncio.FIRST_EXCEPTION
    )

    for task in pending:
        task.cancel()

async def main():
    async with serve(handle_client, None, 8765):
        print("Serveur WebSocket démarré sur le port 8765")
        await asyncio.Future()  # run forever

asyncio.run(main())
