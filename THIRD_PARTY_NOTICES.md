# Third-party software and assets

Our MIT license covers our original contribution. It does not change the terms of the software and assets below.

| Component | Where it is used | Source and terms |
|---|---|---|
| CoppeliaSim | External simulator, installed separately | [Coppelia Robotics](https://www.coppeliarobotics.com/), [licensing](https://manual.coppeliarobotics.com/en/licensing.htm). The Edu edition has educational-use restrictions. |
| Built-in Quadcopter geometry and flight controller | Embedded in the two `.ttt` demonstration scenes; loaded from the reader's installed model library when rebuilding | Coppelia Robotics, [official model collection](https://github.com/CoppeliaRobotics/models/tree/master/robots/mobile). Preserve embedded notices and consult the upstream distribution for asset terms. We do not claim authorship or offer these assets under our MIT license. |
| Default floor, cameras and scene objects | Included in generated CoppeliaSim scenes | Coppelia Robotics distribution; upstream terms apply. |
| `coppeliasim-zmqremoteapi-client` 2.0.4 | Python connection to the simulator | [Official source](https://github.com/CoppeliaRobotics/zmqRemoteApi), BSD license classifier in [package metadata](https://pypi.org/project/coppeliasim-zmqremoteapi-client/2.0.4/). Installed by pip, not vendored. |
| Pillow | Map rendering and PNG export | [Pillow license](https://github.com/python-pillow/Pillow/blob/main/LICENSE). Installed by pip. |
| pyzmq | ZeroMQ sockets, also imported directly in `run.py` | [pyzmq](https://github.com/zeromq/pyzmq). Installed with the connector. Its included notices apply. |
| cbor | Connector serialization | [Package information](https://pypi.org/project/cbor/). Installed with the connector. Its included notices apply. |
| Python and Tk/Tcl | Runtime, standard library and map window | [Python license](https://docs.python.org/3/license.html) and the notices in the installed runtime. |
| ESP-Drone | Future hardware reference only | [Espressif repository](https://github.com/espressif/esp-drone). No ESP-Drone source or firmware is bundled or executed here. |

The simulator executable, plugins, installers and model library are not included. Rebuilding loads the Quadcopter from the reader's own CoppeliaSim installation. Publishing our Python source does not make the complete simulator stack MIT licensed.

Simulator pictures and recorded maps illustrate our project runs. They show an attributed upstream model. The academic presentation and college logo are not part of this software package.

References checked on 24 October 2026. The installed release's terms remain relevant when reproducing the project.
