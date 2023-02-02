"""Implements a simple loop for getting cameras unstuck
and for auto adding them"""
import logging
from functools import partial
from threading import Thread, Event
from typing import Optional

from prusa.connect.printer.camera_configurator import CameraConfigurator
from prusa.connect.printer.camera_controller import CameraController
from .const import CAMERA_SCAN_INTERVAL
from .util import loop_until

log = logging.getLogger("my_camera_configurator")


class CameraGovernor:
    """A module for continually refreshing and adding cameras"""

    def __init__(self, camera_configurator: CameraConfigurator,
                 camera_controller: CameraController) -> None:
        self.camera_configurator = camera_configurator
        self.camera_controller = camera_controller

        self._governance_quit_event = Event()
        self._governance_thread: Optional[Thread] = None

    def _govern(self, auto_detect=True) -> None:
        """Monitors the cameras re-starts failed ones,
        optionally scans for newly connected ones"""
        log.debug("Running the camera governance routine")
        self.camera_controller.disconnect_stuck_cameras()
        self.camera_configurator.load_cameras(auto_detect=auto_detect)

    def start(self, auto_detect=True) -> None:
        """Starts the camera governing loop"""
        self._governance_quit_event.clear()
        target = partial(
            loop_until,
            loop_evt=self._governance_quit_event,
            run_every_sec=lambda: CAMERA_SCAN_INTERVAL,
            to_run=self._govern,
            auto_detect=lambda: auto_detect)

        self._governance_thread = Thread(
            target=target,
            name="camera_governance",
            daemon=True
        )
        self._governance_thread.start()

    def stop(self) -> None:
        """Stops the auto-add loop"""
        self._governance_quit_event.set()

    def wait_stopped(self) -> None:
        """Waits util the component's thread stops"""
        if self._governance_thread is None:
            return
        if self._governance_thread.is_alive():
            self._governance_thread.join()
