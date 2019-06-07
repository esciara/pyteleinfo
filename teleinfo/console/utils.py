import io
import subprocess


def _list_ports():
    """
    Uses pyserial to abtain the list of com port present on the host system.

    Returns: list of ports

    """
    proc = subprocess.Popen(
        ["python -m serial.tools.list_ports"], stdout=subprocess.PIPE, shell=True
    )
    (out, _) = proc.communicate()
    buf = io.StringIO(out.decode("ascii"))
    ports = buf.read().splitlines()
    return ports
