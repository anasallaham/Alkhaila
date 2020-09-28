# -*- coding: utf-8 -*-
"""
Main IP Printer Drivers.

copyright Bernard Tooo <bernard.too@optima.co.ke>.
"""
import base64
import io
import logging
import time

from PIL import Image, ImageOps

from odoo import http

from . import hw_escpos as hwEscpos

try:

    from ..escpos import escpos as Escpos, exceptions as E, printer as Printer
except ImportError:
    Escpos = Printer = None

LOGGER = logging.getLogger(__name__)


class Network(Printer.Network):
    """IP Network printer definition."""

    def _raw(self, msg):
        if isinstance(msg, str):
            msg = msg.encode()  # str to bytes
        self.device.sendall(msg)

    def print_img_receipt(self, receipt):
        """Print the receipt in image format."""
        im = Image.open(io.BytesIO(receipt))

        # Convert to greyscale then to black and white
        im = im.convert("L")
        im = ImageOps.invert(im)
        im = im.convert("1")
        """
        ESC a n
            - ESC a: Select justification, in hex: "1B 61"
            - n: Justification:
                - 0: left
                - 1: center
                - 2: right
        """
        center = b"\x1b\x61\x01"
        """GS v0 m x y
            - GS v0: Print raster bit image, in hex: "1D 76 30"
            - m: Density mode:
                - 0: 180dpi x 180dpi
                - 1: 180dpi x 90dpi
                - 2: 90dpi x 180 dpi
                - 3: 90dpi x 90 dpi
            - x: Length in X direction, in bytes, represented as 2 bytes
            in little endian
            - y: Length in Y direction, in dots, represented as 2 bytes
            in little endian
        """
        width_pixels, height_pixels = im.size
        width_bytes = int((width_pixels + 7) / 8)
        print_command = (
            b"\x1d\x76\x30"
            + b"\x00"
            + (width_bytes).to_bytes(2, "little")
            + height_pixels.to_bytes(2, "little")
        )
        """
        GS V m
            - GS V: Cut, in hex: "1D 56"
            - m: Cut mode:
                - 0: Full cut
                - 1: Partial cut
                - 65 (0x41): Feed paper then full cut
                - 66 (0x42): Feed paper then partial cut
        """
        cut = b"\x1d\x56" + b"\x41"

        self._raw(center + print_command + im.tobytes() + cut + b"\n")

    def open_cashbox(self):
        """Send signal to the current printer to open the connected cashbox."""
        # ESC = --> Set peripheral device
        LOGGER.info("ESC/POS: OPENING CASH DRAWER......................")
        self._raw(b"\x1b\x3d\x01")
        for drawer in [b"\x1b\x70\x00", b"\x1b\x70\x01"]:  # Kick pin 2 and 5
            command = drawer + b"\x19\x19"  # Pulse ON for 50ms then OFF  50ms
            self._raw(command)


class EscposDriver(hwEscpos.EscposDriver):
    """ESC/POS Drivers for IP Printer."""

    def __init__(self, ip, port):
        """IP address and port required to connect to printer."""
        hwEscpos.EscposDriver.__init__(self)
        self.ip = ip
        self.port = int(port)

    def connected_network_devices(self):
        """Define the printer to connect to."""
        connected = {"ip": self.ip, "port": self.port}
        return connected

    def get_escpos_printer(self):
        """Get the IP printer paramters."""
        printers = None
        if self.ip and self.port:
            printers = self.connected_network_devices()
            if printers:
                print_dev = Network(printers["ip"], printers["port"])
                peer = print_dev.device.getpeername()
                self.set_status(
                    "connected",
                    "Connected to printer: %s on port %s" % (peer[0], peer[1]),
                )
                return print_dev
        else:
            printers = self.connected_usb_devices()
            if printers:
                print_dev = Printer.Usb(printers[0]["vendor"], printers[0]["product"])
                self.set_status(
                    "connected",
                    "Connected to %s (in=0x%02x,out=0x%02x)"
                    % (printers[0]["name"], print_dev.in_ep, print_dev.out_ep),
                )
                return print_dev
        self.set_status("disconnected", "Printer Not Found")
        return None

    def run(self):
        """Do the printing job. Override to add python 3 compatibility."""
        printer = None
        if not Escpos:
            LOGGER.error(
                "ESC/POS cannot initialize, please verify system dependencies."
            )
            return
        error = True
        while error:
            try:
                timestamp, task, data = self.queue.get(True)

                printer = self.get_escpos_printer()

                if printer is None:
                    if task != "status":
                        self.queue.put((timestamp, task, data))
                    error = False
                    time.sleep(5)
                    continue
                elif task == "receipt":
                    if timestamp >= time.time() - 1 * 60 * 60:
                        self.print_receipt_body(printer, data)
                        printer.cut()
                elif task == "xml_receipt":
                    if timestamp >= time.time() - 1 * 60 * 60:
                        printer.receipt(data)
                elif task == "img_receipt":
                    if timestamp >= time.time() - 1 * 60 * 60:
                        # printer.set(align='center')
                        # printer.print_base64_image(data)
                        printer.print_img_receipt(base64.decodebytes(data))
                        # printer.cut(mode='full')
                        printer.open_cashbox()
                elif task == "cashbox":
                    if timestamp >= time.time() - 12:
                        self.open_cashbox(printer)
                elif task == "printstatus":
                    self.print_status(printer)
                elif task == "status":
                    pass
                error = False

            except E.NoDeviceError as e:
                LOGGER.info("No device found %s", e)
            except E.HandleDeviceError as e:
                LOGGER.info(
                    "Impossible to handle the device due \
                            to previous error %s",
                    e,
                )
            except E.TicketNotPrinted as e:
                LOGGER.info(
                    "The ticket does not seems to have been \
                            fully printed % s",
                    e,
                )
            except E.NoStatusError as e:
                LOGGER.info("Impossible to get the printer status %s", e)
            except Exception as e:
                self.set_status("error", e)
                LOGGER.exception(e)
            finally:
                self.ip = None
                self.port = None
                if error:
                    self.queue.put((timestamp, task, data))
                if printer:
                    printer.device.close()

    def set_status(self, status, message=None):
        """Set the status of the printer."""
        if not isinstance(message, str):  # python3 compatibility
            message = "%s" % message
        LOGGER.info(status + " : " + (message or "no message"))
        if status == self.status["status"]:
            if message is not None and (
                len(self.status["messages"]) == 0
                or message != self.status["messages"][-1]
            ):
                self.status["messages"].append(message)
        else:
            self.status["status"] = status
            if message:
                self.status["messages"] = [message]
            else:
                self.status["messages"] = []

        if status == "error" and message:
            LOGGER.error("ESC/POS Error: %s", message)
        elif status == "disconnected" and message:
            LOGGER.warning("ESC/POS Device Disconnected: %s", message)


class EscposProxy(hwEscpos.EscposProxy):
    """Routes for printing using IP printer."""

    @http.route("/hw_net_printer/print_img_receipt", type="json", auth="none", cors="*")
    def print_img_receipt(self, **params):
        """Receipt printing method."""
        LOGGER.info("ESC/POS: PRINT IMG RECEIPT USING NETWORK PRINTER......")
        try:
            ip = params.get("ip") or "127.0.0.1"
            port = params.get("port") or 9100
            driver = EscposDriver(ip, port)
            img = params.get("receipt")
            if isinstance(img, str):
                img = img.encode()
            driver.push_task("img_receipt", img)
        except Exception as e:
            return {"error": True, "message": e}
        else:
            return {"error": False, "message": ""}
