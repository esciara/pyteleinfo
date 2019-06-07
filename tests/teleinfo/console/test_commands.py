import asyncio

import pytest
from cleo import CommandTester
from hamcrest import *

from teleinfo.console import Application


@pytest.mark.asyncio
async def test_port_command(slave_name):
    app = Application()

    command = app.find("port")

    print("TEST: tester = CommandTester(command)")
    tester = CommandTester(command)
    print("TEST: tester.execute(slave_name)")
    tester.execute(slave_name)

    print(f"TEST: tester.io.fetch_output(): {tester.io.fetch_output()}")
    print("TEST: assert here")
    assert_that(
        tester.io.fetch_output(),
        contains_string('{"ADCO": "050022120078", "OPTARIF": "HC..",'),
    )
