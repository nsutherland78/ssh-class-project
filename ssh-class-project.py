#!/usr/bin/env python3

from argparse import ArgumentParser
import getpass
import ipaddress
import paramiko
import time
import sys

BUFFER = 524280
TIMEOUT = 4


def create_parser():
    parser = ArgumentParser(
        description='Runs a command against a device or devices'
    )
    parser.add_argument(
        '-d',
        '--device',
        type=str,
        help='Enter an IPv4 Address to run command against a single device.'
    )
    parser.add_argument(
        '-l',
        '--uselist',
        action='store_true',
        help='Use device-list.txt file for list of devices to run commands against.'
    )
    return parser.parse_args()


ARGS = create_parser()


class SSH(object):
    def __init__(self, device, username, password):
        self.device = device
        self.username = username
        self.password = password
        ssh = paramiko.SSHClient()
        # Disable .ssh/known_hosts prompting
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Initiate connection to device, output status
        ssh.connect(device, username=username, password=password, allow_agent=False, look_for_keys=False, timeout=TIMEOUT)
        channel = ssh.invoke_shell()
        self.channel = channel
        self.ssh = ssh

    def disable_pagination(self):
        # Disable pagination
        self.channel.send("term len 0\n")
        time.sleep(TIMEOUT)

    def send_command(self, command):
        # send command
        self.channel.send(command)
        time.sleep(TIMEOUT)
        # Capture the output of command into variable to return
        raw_output = self.channel.recv(BUFFER)
        output = raw_output.decode('utf-8')
        return output

    def clear_buffer(self):
        # Clear buffer
        self.channel.recv(BUFFER)

    def disconnect(self):
        # Disconnect ssh connection
        self.ssh.close()


def main():
    try:
        # Gather login details
        username, password = login()
        # Import device list
        devicelist = device_list()
        command = run_command()
        print("Gathering data...\n")
        for device in devicelist:
            try:
                host = SSH(device, username, password)
                host.disable_pagination()
                host.clear_buffer()
                config = host.send_command(command)
                print(config)
            except Exception as e:
                print(e)
                sys.exit(1)
            finally:
                host.disconnect()
                sys.exit(0)
    except KeyboardInterrupt:
        print("\nUser exited by keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)


def device_list():
    # Gather list of device(s) to run against
    device = ARGS.device
    devicelist = ARGS.uselist
    if device:
        try:
            ipaddress.ip_address(device)
        except Exception as e:
            print(e)
            sys.exit(1)
        devicelist = [device]
    elif devicelist:
        devicelist = import_devices()
    else:
        device = input("Provide device in IPv4 format (e.g. 10.0.0.1): ")
        try:
            ipaddress.ip_address(device)
        except Exception as e:
            sys.exit(1)
        devicelist = [device]
    return devicelist


def run_command():
    # Request command to run against device
    command = input("Provide command to run against device: ") + "\n"
    return command


def import_devices():
    # Open file with device list
    with open('device-list.txt', 'r') as f:
        devicelist = f.read().splitlines()
        f.close()
    return devicelist


def login():
    # Gather username from current session
    username = input("Provide username: ")
    not_same_password = True
    # Ensure user enters correct password
    while not_same_password:
        password1 = ""
        password2 = ""
        password1 = getpass.getpass("Password for {}: ".format(username))
        password2 = getpass.getpass("Retype password for {}: ".format(username))
        if password1 == password2:
            not_same_password = False
        else:
            print("Passwords did not match, please try again;\n\n")
            continue
    return username, password1


if __name__ == '__main__':
    main()
