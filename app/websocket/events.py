import json 

async def send_event(websocket, event, data):

    payload = {
        "event" : event,
        "data" :  data
    }

    await websocket.send_text(
        json.dump(payload)
    )