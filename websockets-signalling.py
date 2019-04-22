#!/usr/local/Cellar/python/3.6.4_4/bin/python3

import asyncio
import websockets
import json

listeners = {}

async def recv(websocket, path):

    linkupIds = []
    defaultLinkupId = path[1:]

    go = True

    print('opened websocket for: ' + defaultLinkupId)

    #sockets[path] = websocket
    while go and websocket.open:
        print('waiting for next message')
        messageRcvd = None
        try:
            messageRcvd = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print('message received, it is: ' + messageRcvd)
        except asyncio.TimeoutError:
            print('timeout waiting for message')
        except:
            print('error waiting for message')


        if messageRcvd:
            message = json.loads(messageRcvd)
            if message['action'] == 'pong':
                print('received pong')
            elif message['action'] == 'listen':
                linkupId = message.get('linkupId', defaultLinkupId)
                if linkupId not in linkupIds:
                    linkupIds.append(linkupId)
                if linkupId not in listeners:
                    listeners[linkupId] = []
                if websocket not in listeners[linkupId]:
                    listeners[linkupId].append(websocket)
                print('registering a listener for ' + linkupId)
            elif message['action'] == 'send':

                receiver = message.get('linkupId', defaultLinkupId)

                print('trying to send a message to ' + receiver)
                if receiver in listeners:
                    to_remove = []
                    for sock in listeners[receiver]:
                        if sock.open:
                            await sock.send(json.dumps(message))
                            print('found listener for ' + receiver + ', sent message')
                        else:
                            to_remove.append(sock)
                    for sock in to_remove:
                        listeners[receiver].remove(sock)
        else:
            if linkupIds:
                print('sending ping')
                try:
                    await websocket.send(json.dumps({'action' : 'ping'}))
                except:
                    print('failed to send ping')
            else:
                go = False
    for linkupId in linkupIds:
        if linkupId in listeners and websocket in listeners[linkupId]:
            print('removing websocket from ' + linkupId)
            listeners[linkupId].remove(websocket)
    print('closing websocket')

start_server = websockets.serve(recv, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
