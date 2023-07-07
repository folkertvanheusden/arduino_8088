#! /usr/bin/python3

# Required: pyserial

# This code was written by Folkert van Heusden and released under the GPLv3 license.

from enum import Enum
import serial
import sys
import time
from typing import Optional, Tuple

class Arduino8088Client:
    class Command(Enum):
        CmdNone = (0x00, 0)
        CmdVersion = (0x01, 0)
        CmdReset = (0x02, 0)
        CmdLoad = (0x03, 28)
        CmdCycle = (0x04, 0)
        CmdReadAddress = (0x05, 0)
        CmdReadStatus = (0x06, 0)
        CmdRead8288Command = (0x07, 0)
        CmdRead8288Control = (0x08, 0)
        CmdReadDataBus = (0x09, 0)
        CmdWriteDataBus = (0x0A, 1)
        CmdFinalize = (0x0B, 0)
        CmdBeginStore = (0x0C, 0)
        CmdStore = (0x0D, 0)
        CmdQueueLen = (0x0E, 0)
        CmdQueueBytes = (0x0F, 0)
        CmdWritePin = (0x10, 2)
        CmdReadPin = (0x11, 1)
        CmdGetProgramState = (0x12, 0)
        CmdLastError = (0x13, 0)
        CmdGetCycleStatus = (0x14, 0)
        CmdInvalid = (0x15, 0)

    def __init__(self, serial_port: str, debug: bool) -> None:
        self.debug = debug

        self.fd = serial.serial_for_url(serial_port, baudrate=1000000, timeout=1.)

    def _send_command(self, command: Command, data: bytearray) -> bool:
        self.fd.write(command.value[0].to_bytes(1, 'big'))

        assert (data is None and command.value[1] == 0) or len(data) == command.value[1]

        if not data is None:
            self.fd.write(data)

        return True

    def _receive_n(self, n) -> Optional[list[int]]:
        rc = [ c for c in self.fd.read(n) ]

        if self.debug:
            print('from serial:', rc, file=sys.stderr)

        if rc[-1] == 0x01:  # ok
            return rc

        if rc[-1] == 0x00:  # error
            if self.debug:
                print('Arduino8088 returned error state', file=sys.stderr)
            return None

        if self.debug:
            print('Arduino8088 out of sync', file=sys.stderr)

        time.sleep(0.11)

        self.fd.flush()

        return None

    # returns (name, versionnumber)
    def cmd_version(self) -> Optional[Tuple[str, int]]:
        if self._send_command(Arduino8088Client.Command.CmdVersion, None) == False:
            return None

        reply = self._receive_n(9)

        if reply == None:
            return None

        return (''.join([ chr(c) for c in reply[0:7] ]), reply[7])

    # returns False for any error, True when the reset succeeded
    def cmd_reset(self) -> bool:
        if self._send_command(Arduino8088Client.Command.CmdReset, None) == False:
            return None

        return self._receive_n(1) == [ 0x01 ]

    # load the registers with a certain value
    def cmd_load(self, AX: int, BX: int, CX: int, DX: int, SS: int, SP: int, FLAGS: int, IP: int, CS: int, DS: int, ES: int, BP: int, SI: int, DI: int) -> bool:
        out = AX.to_bytes(2, 'little')
        out += BX.to_bytes(2, 'little')
        out += CX.to_bytes(2, 'little')
        out += DX.to_bytes(2, 'little')
        out += SS.to_bytes(2, 'little')
        out += SP.to_bytes(2, 'little')
        out += FLAGS.to_bytes(2, 'little')
        out += IP.to_bytes(2, 'little')
        out += CS.to_bytes(2, 'little')
        out += DS.to_bytes(2, 'little')
        out += ES.to_bytes(2, 'little')
        out += BP.to_bytes(2, 'little')
        out += SI.to_bytes(2, 'little')
        out += DI.to_bytes(2, 'little')

        assert len(out) == 28

        if self._send_command(Arduino8088Client.Command.CmdLoad, out) == False:
            return None

        return self._receive_n(1) == [ 0x01 ]

    def cmd_cycle(self) -> bool:
        if self._send_command(Arduino8088Client.Command.CmdCycle, None) == False:
            return None

        return self._receive_n(1) == [ 0x01 ]

    def cmd_read_address(self) -> Optional[int]:
        if self._send_command(Arduino8088Client.Command.CmdReadAddress, None) == False:
            return None

        rc = self._receive_n(4)

        if rc == None:
            return None

        return rc[0] | (rc[1] << 8) | (rc[2] << 16)

    def cmd_read_status(self) -> Optional[int]:
        if self._send_command(Arduino8088Client.Command.CmdReadStatus, None) == False:
            return None

        rc = self._receive_n(2)

        if rc == None:
            return None

        return rc[0]

    def cmd_read_8288_command(self) -> Optional[int]:
        if self._send_command(Arduino8088Client.Command.CmdRead8288Command, None) == False:
            return None

        rc = self._receive_n(2)

        if rc == None:
            return None

        return rc[0]

    def cmd_read_8288_control(self) -> Optional[int]:
        if self._send_command(Arduino8088Client.Command.CmdRead8288Control, None) == False:
            return None

        rc = self._receive_n(2)

        if rc == None:
            return None

        return rc[0]

    # returns a list with the contents of each register (14 of them)
    def cmd_store(self) -> Optional[list[int]]:
        if self._send_command(Arduino8088Client.Command.CmdStore, None) == False:
            return None

        rc = self._receive_n(29)

        if rc == None:
            return None

        out = []

        for i in range(0, 14):
            out.append((rc[i * 2 + 1] << 8) | rc[i * 2 + 0])

        return out

a = Arduino8088Client('/dev/ttyUSB1', True)

print('version', a.cmd_version())
print('reset', a.cmd_reset())
print('load', a.cmd_load(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
print('cycle', a.cmd_cycle())
print('read address', a.cmd_read_address())
print('read status', a.cmd_read_status())
print('read 8288 command', a.cmd_read_8288_command())
print('read 8288 control', a.cmd_read_8288_control())
print('store', a.cmd_store())
