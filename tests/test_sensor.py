# import pytest
# import serial
# from teleinfo import serial_asyncio


# @pytest.mark.asyncio
# # test whether the app correctly adds contract number to
# async def test_extract_frame(slave_name):
#     await receive_frame(slave_name)


# async def receive_frame(slave_name: str):
#     slave_reader, _ = await serial_asyncio.open_serial_connection(
#         url=slave_name, baudrate=1200, bytesize=serial.SEVENBITS,
#         parity=serial.PARITY_EVEN,
#         stopbits=serial.STOPBITS_ONE, rtscts=1)
#     while True:
#         msg = await slave_reader.readline()
#         if msg.rstrip() == 'DONE'.encode('ascii'):
#             break
