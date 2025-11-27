import asyncio
from websockets.server import serve
from websockets.exceptions import ConnectionClosed
import json
from Ultrasonic_Avoidance import Ultrasonic_Avoidance
from concurrent.futures import ThreadPoolExecutor
from Line_Follower import Line_Follower
from SunFounder_PiCar.picar import back_wheels, front_wheels
from SunFounder_PiCar import picar

# 0: Puissance
# 1: Angle
sensor_rate = 20
motor_rate = 30
Ultra = Ultrasonic_Avoidance(17)
Line = Line_Follower()
bw = back_wheels.Back_Wheels(db='config')
fw = front_wheels.Front_Wheels(db='config')
car = {
    "speed": 0,
    "angle": 90
}
fw.turning_max = 45

async def sensor_loop(websocket, alive):
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=1)

    while alive.is_set():
        try:
            distance = await loop.run_in_executor(executor, Ultra.get_distance)
            line_r = await loop.run_in_executor(executor, Line.read_raw)

            data = {
                "UltraValue": distance,
                "Raw": line_r
            }
            
            # Send to Godot
            await websocket.send(json.dumps(data))
            
            await asyncio.sleep(1 / sensor_rate)

        except ConnectionClosed:
            alive.clear()
        except Exception as e:
            print(f"Sensor Error: {e}")
            await asyncio.sleep(0.1) 

async def motor_updater(alive):
    last_speed = 0
    last_angle = -1

    while alive.is_set():
        try:
            target_speed = car["speed"]
            target_angle = car["angle"]

            if target_angle != last_angle:
                fw.turn(target_angle)
                last_angle = target_angle

            if target_speed != last_speed:
                if target_speed < 0:
                    bw.backward()
                    bw.speed = -target_speed
                else:
                    bw.forward()
                    bw.speed = target_speed
                last_speed = target_speed

            await asyncio.sleep(1 / motor_rate)

        except Exception as e:
            print(f"Motor Error: {e}")
            
    bw.speed = 0

async def handle_client(websocket):
    loop = asyncio.get_running_loop()
    alive = asyncio.Event()
    alive.set()

    sensor_task = asyncio.create_task(sensor_loop(websocket, alive))
    motor_task = asyncio.create_task(motor_updater(alive))

    try:
        async for message in websocket:
            try:
                engine = json.loads(message)
                car["speed"] = int(engine["0"])
                car["angle"] = int(engine["1"])
            except ValueError:
                pass
    except ConnectionClosed:
        print("Client closed")
    finally:
        alive.clear()
        await asyncio.gather(sensor_task, motor_task, return_exceptions=True)

async def main():
    picar.setup()
    async with serve(handle_client, None, 8765):
        print("Serveur WebSocket démarré sur le port 8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())