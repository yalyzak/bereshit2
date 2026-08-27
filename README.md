# Bereshit

`bereshit` is a Python game and 3D physics engine module designed to provide a lightweight scene, physics, rendering, and object management framework.

## Features

- 3D vector and quaternion math (`Vector3`, `Quaternion`)
- Physics bodies and collision shapes (`Rigidbody`, `BoxCollider`, `MeshCollider`)
- Constraint joints (`FixedJoint`, `HingeJoint`)
- Scene and world management (`World`, `Physics`)
- Camera and rendering utilities (`Camera`, `MeshRander`, `render`)
- Raycasting and collision detection (`Raycast`, `Collision`)

## Installation

Install the required dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Quick Start

Use `bereshit` by importing the package from the project root:

```python
from bereshit import GameObject, Vector3, Core, Camera, BoxCollider, Rigidbody
from bereshit.addons.essentials import FPS_cam, CamController

cam = GameObject(position=Vector3(0, 0, -8)).add_component(Camera(), CamController(), FPS_cam())

floor = GameObject(size=Vector3(10,1,10), position=Vector3(0,-1,0)).add_component(BoxCollider(), Rigidbody(isKinematic=True))

obj2 = GameObject(position=Vector3(0,2,0)).add_component(BoxCollider(), Rigidbody())

Core.run([cam, floor, obj2])
```

## core class

- `Vector3.py` and `Quaternion.py` for math utilities
- `Object.py` for scene objects
- `Rigidbody.py`, `BoxCollider.py` for simulation logic
- `Camera.py`, `MeshRander.py`, `render.py` for rendering


# bereshit License

Copyright (c) 2026 yaly zak

## 1. Grant of License

Permission is hereby granted to any person obtaining a copy of this software and associated documentation files (the “Software”) to use, copy, modify, merge, publish, and distribute the Software for **non-commercial purposes only**, subject to the following conditions:

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
* Any modifications to the Software must be clearly documented.
* Contributors agree that any submitted code may be used, modified, relicensed, or distributed by the project owner without restriction.

## 2. Non-Commercial Use

“Non-commercial use” includes:

* personal projects
* hobby projects
* educational use
* research
* open-source projects
* game jams
* non-profit projects

provided that no direct or indirect commercial advantage or monetary compensation is involved.

## 3. Commercial Use

Commercial use of the Software is prohibited without prior written permission from the copyright holder.

Commercial use includes, but is not limited to:

* selling games made with the Software
* monetized games or applications
* paid products or services using the Software
* enterprise/internal commercial tools
* SaaS or cloud-hosted products
* commercial publishing agreements

To obtain a commercial license, contact:

yaly.zak@gmail.com

## 4. Contributions

By contributing code, documentation, assets, or other material to this project, you grant the project owner a perpetual, worldwide, non-exclusive, irrevocable right to use, modify, sublicense, and relicense your contributions in both open-source and commercial versions of the Software.

## 5. No Warranty

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE SOFTWARE OR THE USE OF THE SOFTWARE.

