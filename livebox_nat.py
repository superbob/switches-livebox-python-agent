#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import configparser

import livebox4_api


def is_nat_enabled(session, source_port, dest_ip, dest_port):
    forwardings = livebox4_api.get_port_forwardings(session)
    for key, value in forwardings.items():
        external_port = value['ExternalPort']
        dest_ip_address = value['DestinationIPAddress']
        internal_port = value['InternalPort']
        if external_port == str(source_port) and internal_port == str(dest_port) and dest_ip_address == dest_ip:
            return True
    return False


def enable_nat(session, source_port, dest_ip, dest_port):
    if not is_nat_enabled(session, source_port, dest_ip, dest_port):
        livebox4_api.add_port_forwarding(session, "webui_ssh-raspi", source_port, dest_port, dest_ip)


def disable_nat(session, source_port, dest_ip, dest_port):
    forwardings = livebox4_api.get_port_forwardings(session)
    nat_id = None
    for key, value in forwardings.items():
        external_port = value['ExternalPort']
        dest_ip_address = value['DestinationIPAddress']
        internal_port = value['InternalPort']
        if external_port == str(source_port) and internal_port == str(dest_port) and dest_ip_address == dest_ip:
            nat_id = key
    if nat_id is not None:
        livebox4_api.remove_port_forwarding(session, dest_ip, nat_id)


def get_public_ip():
    return livebox4_api.get_wan_ip()


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    password = config.get('livebox-api', 'password')
    source_port = config.get('livebox-api', 'source-port')
    target_ip = config.get('livebox-api', 'target-ip')
    target_port = config.get('livebox-api', 'target-port')

    session = livebox4_api.create_session(password)
    nat_enabled = is_nat_enabled(session, source_port, target_ip, target_port)

    livebox4_api.invalidate_session(session)

    if nat_enabled:
        print("Nat is enabled")
    else:
        print("Nat is not enabled")


if __name__ == '__main__':
    main()
