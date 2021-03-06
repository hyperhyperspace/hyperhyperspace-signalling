#!/usr/local/Cellar/python/3.7.3/bin/python3

import asyncio
import websockets
import json
import random

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
                limit    = message.get('limit', None)

                print('trying to send a message to ' + receiver)
                #sent = False;
                if receiver in listeners:
                    to_remove = []
                    all_socks = listeners[receiver]
                    sock_targets = random.sample(all_socks, min(limit, len(all_socks))) if limit else all_socks

                    for sock in sock_targets:
                        if sock.open:
                            await sock.send(json.dumps(message))
                            print('found listener for ' + receiver + ', sent message')
                        else:
                            to_remove.append(sock)
                    for sock in to_remove:
                        listeners[receiver].remove(sock)
                    #if not sent:
                    #    try:
                    #        websocket.send(json.dumps({'action': 'nack', 'linkupId': message['reply'], 'missingLinkupId': receiver}))
                    #        print('could not find listener for ' + receiver + ', sending nack')
                    #    except:
                    #        print('failed to send nack')
            elif message['action'] == 'query':
                targets = message['linkupIds']
                queryId = message['queryId']
                hits = []
                for target in targets:
                    if target in listeners:
                        for sock in listeners[target]:
                            if sock.open:
                                hits.append(target)
                                break
                print('replying to query with id ' + queryId + ' with results: ' + str(hits))
                await websocket.send(json.dumps({'action': 'query-reply', 'queryId': queryId, 'hits': hits}))

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