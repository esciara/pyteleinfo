from cleo import CommandTester
from hamcrest import *

from teleinfo.console import Application


def test_port_command(slave_with_dirty_first_frame):
    app = Application()
    command = app.find("port")
    tester = CommandTester(command)
    tester.execute(slave_with_dirty_first_frame)
    assert_that(
        tester.io.fetch_output(),
        contains_string('{"ADCO": "050022120078", "OPTARIF": "HC..",'),
    )
