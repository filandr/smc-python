import json
import time
import logging
import websocket
from websocket._exceptions import WebSocketTimeoutException
from smc import session
from pprint import pformat

logger = logging.getLogger(__name__)


class FetchAborted(Exception):
    pass

class FetchFailed(Exception):
    pass


def websocket_query(query, timeout=60, sock_sleep=5):
    ses_mon_ws=session.web_socket_url + query.location
    
    if logger.getEffectiveLevel() == logging.DEBUG: 
        websocket.enableTrace(True)
    ws = websocket.create_connection(
        ses_mon_ws,
        header={'Cookie': session.session_id},
        timeout=timeout)
    
    fetch_id = None
    try:
        logger.debug(pformat(query.request))
        ws.send(json.dumps(query.request))
    
        # First message is status of query
        data = ws.recv()
        fetch = json.loads(data)
        
        if 'failure' in fetch:
            ws.close()
            raise FetchFailed(fetch['failure'])
        
        if 'fields' in fetch:
            yield {'fields' : fetch['fields']}
            
        logger.debug('%s: Waiting for web socket results.', fetch['success'])
        fetch_id = fetch['fetch']
        
        if query.fetch_size == 0: # Explicit that we want no results, so send abort
            raise FetchAborted('Aborting due to fetch size of 0.')
            
        # First and maybe only payload
        data = ws.recv()
        response = json.loads(data)
        
        print('fetch result: %s' % response)
        if 'status' in response:
            logger.info(response['status'])
            
            #Flush first recv
            if 'records' in response:
                yield response
        
            while response['status'].startswith('Query'):
                #print("Sleeping")
                time.sleep(sock_sleep)
                data = json.loads(ws.recv())
                
                if 'records' in data and data['records']:
                    yield data
                
                if 'end' in data:
                    break
            
        elif 'end' in response: # Small enough fetch to have data on first recv
            yield response
        
        elif 'records' in response: # Session monitoring query
            print("YIELDING RESPONSE")
            yield response
    
    except KeyboardInterrupt:
        pass
    except FetchAborted as e:
        logger.info(e)
    except WebSocketTimeoutException as e:
        logger.error('Websocket timeout: %s', e)
    finally:
        if ws.connected:
            ws.send(json.dumps({'abort': fetch_id}))
            data = ws.recv()
            logger.info(data)
            ws.close()
    
    if not ws.connected:
        logger.info('Successfully closed web socket monitoring.')
