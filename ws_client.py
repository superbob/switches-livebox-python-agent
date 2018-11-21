#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import json
import sys
import logging.config

import websocket

import google_id_token
import livebox4_api
import livebox_nat


PING_COMMAND = 'PING'
PONG_COMMAND = 'PONG'
GET_STATUS_COMMAND = 'GET status'
SET_NAT_SSH_COMMAND_PREFIX = 'SET nat-ssh '
ERROR_COMMAND_PREFIX = 'ERROR '
INFO_COMMAND_PREFIX = 'INFO '
STATUS_COMMAND_FORMAT = "STATUS {status_payload}"

LOGGING_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
logging.config.dictConfig(LOGGING_CONF)
logger = logging.getLogger('ws_client')


def authenticate(ws, service_account_file, audience):
    """Authenticates the WebSocket"""
    ws.send("Bearer {token}".format(token=google_id_token.get_id_token(service_account_file, audience)))


def get_status(router_password, source_port, dest_ip, dest_port):
    wan_ip = livebox_nat.get_public_ip()
    session = livebox4_api.create_session(router_password)
    enabled = livebox_nat.is_nat_enabled(session, source_port, dest_ip, dest_port)
    livebox4_api.invalidate_session(session)
    return {'ip_addr': wan_ip, 'ssh_nat_enable': enabled}


def set_nat_rule(router_password, source_port, dest_ip, dest_port, enable):
    session = livebox4_api.create_session(router_password)
    already_enabled = livebox_nat.is_nat_enabled(session, dest_ip)
    if not already_enabled and enable:
        livebox_nat.enable_nat(session, source_port, dest_ip, dest_port)
    elif already_enabled and not enable:
        livebox_nat.disable_nat(session, source_port, dest_ip, dest_port)
    wan_ip = livebox_nat.get_public_ip()
    then_enabled = livebox_nat.is_nat_enabled(session, source_port, dest_ip, dest_port)
    livebox4_api.invalidate_session(session)
    return {'ip_addr': wan_ip, 'ssh_nat_enable': then_enabled}


def handle_message(ws, message, router_password, source_port, dest_ip, dest_port):
    if message == PING_COMMAND:
        logger.debug('Received ping message, replying with pong.')
        ws.send(PONG_COMMAND)
    else:
        logger.debug("Received message: \"{message}\".".format(message=message))
        if message == GET_STATUS_COMMAND:
            logger.info('Replying with status.')
            ws.send(STATUS_COMMAND_FORMAT.format(status_payload=json.dumps(get_status(router_password, source_port, dest_ip, dest_port))))
        elif message.startswith(SET_NAT_SSH_COMMAND_PREFIX):
            requested_state = message[len(SET_NAT_SSH_COMMAND_PREFIX):]
            value = json.loads(requested_state)
            logger.info("Changing nat rule if needed with {value}".format(value=value))
            result = set_nat_rule(router_password, dest_ip, value)
            ws.send(STATUS_COMMAND_FORMAT.format(status_payload=json.dumps(result)))
        elif message.startswith(ERROR_COMMAND_PREFIX):
            payload = message[len(ERROR_COMMAND_PREFIX):]
            logger.error(payload)
        elif message.startswith(INFO_COMMAND_PREFIX):
            payload = message[len(INFO_COMMAND_PREFIX):]
            logger.info(payload)
        else:
            logger.error("Could not handle message: {message}".format(message=message))


def setup_websocket(ws_url, service_account_file, audience, router_password, source_port, dest_ip, dest_port):
    """Configures and start the WebSocket"""
    def on_message(ws, message):
        """Handle a message"""
        handle_message(ws, message, router_password, source_port, dest_ip, dest_port)

    def on_error(ws, error):
        """Handle an error by exiting or closing if it is a KeyboardInterrupt (Ctrl+C)"""
        if type(error) is KeyboardInterrupt:
            logger.info('Cancel requested (Ctrl+C), closing connection.')
            ws.close()
        else:
            logger.error("The following error occurred:\n{error}".format(error=error))
            sys.exit(1)

    def on_close(ws):
        """Handle the WebSocket close"""
        logger.info('WebSocket closed.')

    def on_open(ws):
        """Handle the WebSocket opening"""
        logger.info('WebSocket open, sending authentication.')
        authenticate(ws, service_account_file, audience)
        ws.send(STATUS_COMMAND_FORMAT.format(status_payload=json.dumps(get_status(router_password, source_port, dest_ip, dest_port))))

    return websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    logger.info('Starting agent')

    ws = setup_websocket(
        config.get('bridge', 'ws-url'),
        config.get('google-id', 'service-account-file'),
        config.get('google-id', 'audience'),
        config.get('livebox-api', 'password'),
        config.get('livebox-api', 'source-port'),
        config.get('livebox-api', 'target-ip'),
        config.get('livebox-api', 'target-port'))

    ws.run_forever()
