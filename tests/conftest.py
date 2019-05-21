# content of conftest.py
import os
import pty
import asyncio

import pytest

VALID_FRAME = ["ADCO 524563565245 /\n",
               "OPTARIF HC.. <\n",
               "ISOUSC 20 8\n",
               "HCHC 001065963 _\n",
               "HCHP 001521211 '\n",
               'PTEC HC.. S\n',
               'IINST 001 I\n',
               'IMAX 008 2\n',
               'PMAX 06030 3\n',
               'PAPP 01250 +\n',
               'HHPHC E 0\n',
               'MOTDETAT 000000 B\n',
               'PPOT 00 #\n',
               'ADCO 524563565245 /\n',
               'OPTARIF HC.. <\n',
               'ISOUSC 20 8\n']

VALID_FRAME_DICT = {'ADCO': '524563565245',
                    'OPTARIF': 'HC..',
                    'ISOUSC': '20',
                    'HCHC': '001065963',
                    'HCHP': '001521211',
                    'PTEC': 'HC..',
                    'IINST': '001',
                    'IMAX': '008',
                    'PMAX': '06030',
                    'PAPP': '01250',
                    'HHPHC': 'E',
                    'MOTDETAT': '000000',
                    'PPOT': '00'}


@pytest.fixture
async def slave_name():
    master, slave = pty.openpty()  # open the pseudoterminal
    slave_name = os.ttyname(slave)
    send_task: asyncio.Future = asyncio.ensure_future(send(master, VALID_FRAME))
    yield slave_name
    send_task.cancel()


async def send(master, valid_frame):
    while True:
        for msg in valid_frame:
            os.write(master, msg.encode('ascii'))
            await asyncio.sleep(0)
        os.write(master, 'DONE\n'.encode('ascii'))
