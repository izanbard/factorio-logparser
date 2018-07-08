#!/usr/bin/env python
import threading
import queue
import subprocess
import re
import json
import argparse
import os
import sys
import signal
import time
import datetime
import requests

TIMESTAMP = r'(?P<date>\d+-\d+-\d+)\s+(?P<time>\d+:\d+:\d+)'
SPACE = r'\s+'
COMMAND = r'\[(?P<action>JOIN|LEAVE|KICK|BAN|COMMAND|CHAT)\]'
USERNAME = r'(?P<username>[^\s]+)'
MESSAGE = r'(?P<message>.*)'
ENTRY = TIMESTAMP + SPACE + COMMAND + SPACE + USERNAME + SPACE + MESSAGE
KICK_MESSAGE = r'was kicked by (?P<by>[^.\s]+)\. Reason: (?:unspecified|(?P<reason>.*))\.'
BAN_MESSAGE = r'was banned by (?P<by>[^.\s]+)\. Reason: (?:unspecified|(?P<reason>.*))\.'


class Server:

    def __init__(self, discord_hook):
        self.users = {}
        self.discord_hook = discord_hook

    def process_entry(self, info):
        if (info['action'] == 'JOIN'):
            self.user_login_event(info, True)
        elif (info['action'] == 'LEAVE'):
            self.user_login_event(info, False)
        elif (info['action'] == 'KICK'):
            self.user_kicked(info)
        elif (info['action'] == 'BAN'):
            self.user_banned(info)
        elif (info['action'] == 'COMMAND'):
            self.user_command(info)
        elif (info['action'] == 'CHAT'):
            self.user_chat(info)

    def user_login_event(self, info, is_log_in):
        if not (info['username'] in self.users.keys()):
            self.users[info['username']] = {}
        self.users[info['username']]['online'] = is_log_in
        self.users[info['username']]['last_seen'] = info['date'] + ' ' + info['time']
        if self.discord_hook is not None:
            self.__discord_call(info['username'] + ' has logged in')

    def user_kicked(self, info):
        self.user_login_event(info, False)
        if not ('kicks' in self.users[info['username']].keys()):
            self.users[info['username']]['kicks'] = []
        regex = re.compile(KICK_MESSAGE)
        kick_details = regex.match(info['message']).groupdict()
        self.users[info['username']]['kicks'].extend([[
            info['date'] + ' ' + info['time'],
            kick_details['by'],
            kick_details['reason']
        ]])
        if self.discord_hook is not None:
            self.__discord_call(info['username'] + ' was kicked by' +kick_details['by'])

    def user_banned(self, info):
        self.user_login_event(info, False)
        if not ('bans' in self.users[info['username']].keys()):
            self.users[info['username']]['bans'] = []
        regex = re.compile(BAN_MESSAGE)
        ban_details = regex.match(info['message']).groupdict()
        self.users[info['username']]['kicks'].extend([[
            info['date'] + ' ' + info['time'],
            ban_details['by'],
            ban_details['reason']
        ]])
        if self.discord_hook is not None:
            self.__discord_call(info['username'] + ' was banned by ' + ban_details['by'])

    def user_command(self, info):
        self.user_login_event(info, True)
        self.users[info['username']]['last_command'] = info['message']
        if self.discord_hook is not None:
            self.__discord_call(info['username'] + ' commanded ' + info['message'])

    def user_chat(self, info):
        info['username'] = info['username'][:-1]
        self.user_login_event(info, True)
        self.users[info['username']]['last_chat'] = info['message']
        if self.discord_hook is not None:
            self.__discord_call(info['username'] + ' said ' + info['message'])

    def __discord_call(self, message):
        headers = {'content-type': 'application/json'}
        payload = {
            'content': message,
            'username': 'FactoBot'
        }
        r = requests.post(self.discord_hook, json=payload, headers=headers)
        if not r.status_code == 204:
            print(r.text)


def tail_forever(filename, queue, tailing):
    """Tail specified file forever, put read lines on queue."""
    if not os.access(filename, os.R_OK):
        print("Unable to read ", filename)
        tailing[0] = False
    try:
        cmd = ['tail', '-F', '-n', '+1', filename]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while 1:
            line = p.stdout.readline()
            queue.put(line.decode("utf-8"))
            if not line:
                break
    except Exception as e:
        tailing[0] = False


def signal_handler(signal, frame):
    print('Shutting down')
    sys.exit(0)


def report_status(outputfile, frequency, server, tailing):
    """Output JSON with current status/state with assigned frequency"""
    try:
        status = {
            'generated': datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'users': server.users
        }

        status_json = json.dumps(status, indent=4, sort_keys=True)
        status_file = open(outputfile, 'w')
        status_file.write(status_json)
        status_file.close()
    except Exception as e:
        # TODO: Handle exceptions?
        print("Error reporting status: ", e)
    finally:
        if tailing[0]:
            reporting_thread = threading.Timer(frequency, report_status, [outputfile, frequency, server, tailing])
            reporting_thread.daemon = True
            reporting_thread.start()


def main(options):
    server = Server(options.discord)
    console_tail = queue.Queue()
    signal.signal(signal.SIGINT, signal_handler)
    tailing = [True]
    tail_thread = threading.Thread(
        target=tail_forever,
        args=(options.logfile, console_tail, tailing)
    )
    tail_thread.daemon = True
    tail_thread.start()
    report_status(options.outputfile, options.frequency, server, tailing)
    regex = re.compile(ENTRY)
    while tailing[0]:
        try:
            line = console_tail.get_nowait()
            info_obj = regex.match(line)
            if not info_obj is None:
                info = info_obj.groupdict()
                server.process_entry(info)
        except queue.Empty:
            time.sleep(0.5)
        except Exception as e:
            print("Failed attempting to parse line: ", e.args)
            print("Exception: ", e.args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile',
                        help="absolute path to factorio console log eg /opt/factorio/console.log")
    parser.add_argument('-o', '--outputfile',
                        help="absolute path to status output file")
    parser.add_argument('-f', '--frequency', type=float,
                        help="frequency in seconds for reporting status")
    parser.add_argument('-d', '--discord',
                        help="Discord Webhook URL")

    options = parser.parse_args()
    sys.exit(main(options))
