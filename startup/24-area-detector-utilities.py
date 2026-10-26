#TODO: integrate PV to turn on the power supply. ##'XF:11BMB-VA{Chm:Det}UserButton'

print(f'Loading {__file__}')

from ophyd import EpicsSignal

# import telnetlib
# import paramiko
# # import numpy as np
# # SSH connection details
# # hostname = 'xf11bm-pilatus800k2'
# hostname = 'xf11bm-pilatus800k'
# username = 'det'
# password = 'Pilatus2'
# # Create an SSH client
# client = paramiko.SSHClient()
# client.load_system_host_keys()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())



# telnet_command = 'telnet localhost 20002'

# def restartWAXS():


#     try:
#         # Connect to the SSH server
#         client.connect(hostname=hostname,username=username, password=password)


#         command_to_run = './start_camserver'  # Replace this with your desired command
#         stdin, stdout, stderr = client.exec_command(command_to_run)
#     #    output = stdout.read().decode()
#     #    print(output)
#         # Start an interactive shell session
#         ssh_shell = client.invoke_shell()

#         # Send the Telnet command to the shell
#         ssh_shell.send(telnet_command + '\n')

#         # Create a Telnet session on the SSH server
#         tn = telnetlib.Telnet()

#         # Attach the shell transport to the Telnet session
#         tn.sock = ssh_shell

#         ssh_shell.send('\x18\x18')
#         # Read and monitor the output of the Telnet command

#         start_time=time.time()

#         while time.time()-start_time<30:
#             output = tn.read_very_eager().decode()
#             if output:
#                 print(output, end='')

#             # Check if the Telnet connection is closed
#             if tn.eof:
#                 break
#             # if time.time()-start_time>3:
#             #     break
        
#         # Close the SSH connection
#         client.close()

#     finally:
#         # Close the SSH connection
#         client.close()

# def startWAXS(wait_time =10):

#     caput(' XF:11BMB-VA{Chm:Det}UserButton', 1)


#     # #telnet and restart camserver
#     # restartWAXS()
#     time.sleep(wait_time)

#     # swtich to monitor detector status by CSS
#     caput("XF:11BM-CT{Det-P300K:2}Camserver:Restart", 1)
#     #set exposure time twice to garantee the EPICS connection
#     # pilatus300.cam.acquire_time.set(1.3)
#     time.sleep(5)
#     # pilatus300.cam.acquire_time.set(1.7)
#     caput("XF:11BM-ES{Det-P300K:2}:SysReset", 1)

# Restart Pilatus300 after pumping the vacuum below 0.5 mbar.

power_button = EpicsSignal(
    "XF:11BMB-VA{Chm:Det}UserButton", name="waxs_power_button"
)
camserver_restart = EpicsSignal(
    "XF:11BM-CT{Det-P300K:2}Camserver:Restart", name="waxs_camserver_restart"
)
system_reset = EpicsSignal(
    "XF:11BM-ES{Det-P300K:2}:SysReset", name="waxs_system_reset"
)

def _startWAXS_plan(wait_time):
    detector_state = pilatus300.cam.detector_state
    power_button = EpicsSignal(
        "XF:11BMB-VA{Chm:Det}UserButton", name="waxs_power_button"
    )
    camserver_restart = EpicsSignal(
        "XF:11BM-CT{Det-P300K:2}Camserver:Restart", name="waxs_camserver_restart"
    )
    system_reset = EpicsSignal(
        "XF:11BM-ES{Det-P300K:2}:SysReset", name="waxs_system_reset"
    )

    yield from bps.abs_set(power_button, 1, wait=True)
    yield from bps.sleep(wait_time)
    yield from bps.abs_set(camserver_restart, 1, wait=True)
    yield from bps.sleep(5)
    yield from bps.abs_set(system_reset, 1, wait=True)
    yield from bps.sleep(5)

    while True:
        if not detector_state.connected:
            yield from bps.sleep(0.5)
            continue

        state = yield from bps.rd(detector_state)
        if state == 0:
            break
        yield from bps.sleep(0.5)
    print("Pilatus300 detector is ready.")


def startWAXS(wait_time=10):
    """Power and restart Pilatus300, then wait for it to become idle."""
    RE(_startWAXS_plan(wait_time))


        

# try:
#      # Connect to the SSH server
#     client.connect(hostname=hostname,username=username, password=password)


#     command_to_run = './start_camserver'  # Replace this with your desired command
#     stdin, stdout, stderr = client.exec_command(command_to_run)
# #    output = stdout.read().decode()
# #    print(output)
#     # Start an interactive shell session
#     ssh_shell = client.invoke_shell()

#     # Send the Telnet command to the shell
#     ssh_shell.send(telnet_command + '\n')

#     # Create a Telnet session on the SSH server
#     tn = telnetlib.Telnet()

#     # Attach the shell transport to the Telnet session
#     tn.sock = ssh_shell

#     ssh_shell.send('\x18\x18')
#     # Read and monitor the output of the Telnet command

#     start_time=time.time()

#     while time.time()-start_time<30:
#         output = tn.read_very_eager().decode()
#         if output:
#             print(output, end='')

#         # Check if the Telnet connection is closed
#         if tn.eof:
#             break
#         # if time.time()-start_time>180:
#         #     command_to_close = './killall telnet'  # Replace this with your desired command
#         #     stdin, stdout, stderr = client.exec_command(command_to_close)
#         #     output=stdout.read().decode()
#         #     print(output)
#             # tn.write(b'x1d')D
#         # if time.time()-start_time>3:
#         #     break
    
#     tn.close()

# finally:
#     # Close the SSH connection
#     # client.close()
#     client.close()
