import asyncio
import threading
import time
# from builtins import range

from bereshit import render

from bereshitCore import GameObject, Vector3, World


# import old_render as render


def run(scene,speed=1, gizmos=False, scriptRefreshRate=None,tick=1/60, Render=True, ForceRenderInitialize=True, gravity=Vector3(0,-9.8,0), physics_epochs=10, scale=1, MaxTime=None):
    Exit = [False]
    if not Render:
        ForceRenderInitialize = False
    if scriptRefreshRate is None:
        scriptRefreshRate = 2
    else:
        scriptRefreshRate = scriptRefreshRate / tick
    print(scriptRefreshRate)
    TARGET_FPS = 60
    # bereshit.dt = TARGET_FPS * 0.000165

    if not isinstance(scene, list):
        scene = [scene]
    if gizmos:
        hit_points = [GameObject(Vector3(100,100,100), Vector3(0,0,0), Vector3(0.1,0.1,0.1)) for i in range(100)]
        gizmos_container = GameObject(Vector3(0,0,0), Vector3(0,0,0), Vector3(0,0,0),hit_points)
        world = World(Exit[0], scene+[gizmos_container], gizmos_container, gravity, tick, speed, physics_epochs)

    else:
        world = World(Exit[0], scene, GameObject(), gravity, tick, speed, physics_epochs)


    async def main_logic(Initialize, MaxTime=None):
        start_wall_time = time.perf_counter()
        steps = 0
        startedTime = time.perf_counter()
        # speed = 1  # real time slip
        # bereshit.dt = (10 / ((1 / dt) / 60) * speed)
        while not Initialize[0]:
            await asyncio.sleep(0.01)
        world.Start()
        while not Exit[0]:
            steps += 1
            simulated_time = steps * world.tick

            if MaxTime is not None and simulated_time >= MaxTime:
                print(f"Stopping simulation: reached MaxTime ({MaxTime})")
                print(f"simulated time escaped: {simulated_time}")
                print(f"real time escaped: {time.perf_counter() - startedTime}")
                world.Exit()
                exit()

            if steps % scriptRefreshRate == 0:
                world.update(True)
            else:
                # Update simulation
                world.update()

            # Compute when, in wall clock time, this simulated time should happen
            # For double speed: simulated_time advances twice as fast as real time
            target_wall_time = start_wall_time + (simulated_time / world.speed)
            now = time.perf_counter()
            sleep_time = target_wall_time - now

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        if Exit[0]:
            exit()

    def start_async_loop(Initialize=[True], MaxTime=None):
        asyncio.run(main_logic(Initialize, MaxTime))

    if Render:
        if ForceRenderInitialize:
            Initialize = [False]

            logic_thread = threading.Thread(target=start_async_loop, daemon=True, args=([Initialize], MaxTime))
            logic_thread.start()
            # Start rendering in main thread
            render.run_renderer(world,Initialize, Exit)
        else:
            logic_thread = threading.Thread(target=start_async_loop, daemon=True, args=(MaxTime))
            logic_thread.start()

            # Start rendering in main thread
            render.run_renderer(world)
    else:
        start_async_loop(MaxTime=MaxTime)

def run_max_speed(scene, scriptRefreshRate=None, tick=1 / 60, Render=True, ForceRenderInitialize=True,
                  gravity=Vector3(0, -9.8, 0), physics_epochs=10, MaxTime=None):
    Exit = [False]
    if not Render:
        ForceRenderInitialize = False
    if scriptRefreshRate is None:
        scriptRefreshRate = 2
    else:
        scriptRefreshRate = scriptRefreshRate / tick

    if not isinstance(scene, list):
        scene = [scene]

    world = World(Exit[0], scene, GameObject(), gravity, tick, 1, physics_epochs)

    def main_logic(Initialize, MaxTime=None):
        steps = 0
        startedTime = time.perf_counter()
        while not Initialize[0]:
            time.sleep(0.001)
        world.Start()
        while not Exit[0]:
            steps += 1
            simulated_time = steps * world.tick

            if MaxTime is not None and simulated_time >= MaxTime:
                print(f"Stopping simulation: reached MaxTime ({MaxTime})")
                print(f"simulated time escaped: {simulated_time}")
                realTime = time.perf_counter() - startedTime
                print(f"real time escaped: {realTime}")
                print(f"average speed: {simulated_time/realTime}")
                world.Exit()
                exit()

            if steps % scriptRefreshRate == 0:
                world.update(True)
            else:
                # Update simulation
                world.update()
        if Exit[0]:
            exit()

    def start_async_loop(Initialize=[True], MaxTime=None):
        main_logic(Initialize, MaxTime)

    if Render:
        if ForceRenderInitialize:
            Initialize = [False]

            logic_thread = threading.Thread(target=start_async_loop, daemon=True, args=([Initialize], MaxTime))
            logic_thread.start()
            # Start rendering in main thread
            render.run_renderer(world, Initialize, Exit)
        else:
            logic_thread = threading.Thread(target=start_async_loop, daemon=True, args=(MaxTime))
            logic_thread.start()

            # Start rendering in main thread
            render.run_renderer(world)
    else:
        start_async_loop(MaxTime=MaxTime)