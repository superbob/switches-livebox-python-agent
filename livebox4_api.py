#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import requests

DEFAULT_ROUTER_IP = '192.168.1.1'


def get_wan_ip(ip=DEFAULT_ROUTER_IP):
    post_response = requests.post(
        url="http://{ip}/ws".format(ip=ip),
        headers={
            'Content-Type': 'application/x-sah-ws-4-call+json'},
        json={
            'service': 'NMC',
            'method': 'getWANStatus',
            'parameters': {}})
    return post_response.json()['data']['IPAddress']


def create_session(password, ip=DEFAULT_ROUTER_IP, user='admin'):
    post_response = requests.post(
        url="http://{ip}/ws".format(ip=ip),
        headers={
            'Authorization': 'X-Sah-Login',
            'Content-Type': 'application/x-sah-ws-4-call+json'},
        json={
            'service': 'sah.Device.Information',
            'method': 'createContext',
            'parameters': {
                'applicationName': 'so_sdkut',
                'username': user,
                'password': password}})
    if post_response.status_code != 200:
        raise Exception("Request failed with '{status_code}' response code"
                        .format(status_code=post_response.status_code))
    return post_response.json()['data']['contextID'], post_response.cookies


def invalidate_session(session, ip=DEFAULT_ROUTER_IP):
    token, cookies = session
    post_response = requests.post(
        url="http://{ip}/ws".format(ip=ip),
        headers={
            'Authorization': "X-Sah-Logout {token}".format(token=token),
            'Content-Type': 'application/x-sah-ws-4-call+json'},
        cookies=cookies,
        json={
            'service': 'sah.Device.Information',
            'method': 'releaseContext',
            'parameters': {
                'applicationName': 'so_sdkut'}})
    if post_response.status_code != 200:
        raise Exception("Request failed with '{status_code}' response code"
                        .format(status_code=post_response.status_code))
    return post_response.json()['status'] == 0


def get_port_forwardings(session, ip=DEFAULT_ROUTER_IP):
    post_response = session_service_call(ip, session, 'Firewall', 'getPortForwarding', {'origin': 'webui'})
    return post_response.json()['status']


def add_port_forwarding(session, id, source_port, dest_port, dest_ip, ip='192.168.1.1'):
    post_response = session_service_call(
        ip, session, 'Firewall', 'setPortForwarding',
        {
            'id': id,
            'internalPort': str(dest_port),
            'externalPort': str(source_port),
            'destinationIPAddress': dest_ip,
            'enable': True,
            'persistent': True,
            'protocol': '6',
            'description': id,
            'sourceInterface': 'data',
            'origin': 'webui'
        })
    # TODO add some error handling
    return post_response.json()


def remove_port_forwarding(session, id, dest_ip, ip=DEFAULT_ROUTER_IP):
    post_response = session_service_call(
        ip, session, 'Firewall', 'deletePortForwarding',
        {
            'id': id,
            'destinationIPAddress': dest_ip,
            'origin': 'webui'
        })
    if not post_response.json()['status']:
        raise Exception('Request failed with error')


def session_service_call(ip, session, service, method, parameters):
    token, cookies = session
    post_response = requests.post(
        url='http://{ip}/ws'.format(ip=ip),
        headers={
            'Authorization': "X-Sah {token}".format(token=token),
            'Content-Type': 'application/x-sah-ws-4-call+json'},
        cookies=cookies,
        json={
            'service': service,
            'method': method,
            'parameters': parameters})
    return post_response


def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    password = config.get('livebox-api', 'password')

    print("WAN IP: {wan_ip}".format(wan_ip=get_wan_ip()))
    session = create_session(password)
    forwardings = get_port_forwardings(session)
    print("Port forwardings:")
    for key, value in forwardings.items():
        external_port = value['ExternalPort']
        dest_ip_address = value['DestinationIPAddress']
        internal_port = value['InternalPort']
        description = value['Description']
        print("[{key:<15}] (:{external_port} -> {dest_ip_address}:{internal_port}) \"{description}\"".format(key=key, external_port=external_port, dest_ip_address=dest_ip_address, internal_port=internal_port, description=description))

    invalidate_session(session)


if __name__ == '__main__':
    main()
