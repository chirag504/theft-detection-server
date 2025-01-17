from fastapi import FastAPI
import motor.motor_asyncio
import socketio
import datetime
import requests
from azureml.fsspec import AzureMachineLearningFileSystem
import os
import cv2
import numpy as np
import requests
import base64
import io

app = FastAPI()

# STATIC_API_URL = "https://ams-backend-bdx5.onrender.com"

origins = [
    "http://localhost:3000", "https://alumni-mapping-system.vercel.app", "https://ams-backend-bdx5.onrender.com"
]

sio = socketio.AsyncServer(cors_allowed_origins=origins, async_mode='asgi')
socket_app = socketio.ASGIApp(sio)
app.mount("/", socket_app)


@app.get("/")
def read_root():
    return {"Chat": "Opened"}


@sio.event
async def connect(sid): # , environ, alumni
    # await sio.enter_room(sid, alumni)
    print(sid, "connected")
    # print(alumni)


@sio.event
def disconnect(sid):
    print(sid, "disconnected")


@sio.on('send_video')
async def connect_to_storage_and_download_video(sid, connection_string, video_path):
    fs = AzureMachineLearningFileSystem(connection_string)
    fs.get(video_path, f'./vids/')

    file_name = video_path.split('/')[-1]
    local_path = f'vids/{file_name}'

    cap = cv2.VideoCapture(local_path)
    frames = []
    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()
        if success:
            if len(frames) < 40:
                frames.append(frame)
            else:
                # send the frames to the model 
                buffer = io.BytesIO()
                np.save(buffer, frames)
                buffer.seek(0)
                encoded_frames = base64.b64encode(buffer.read()).decode('utf-8')
                payload = {
                    'frames': encoded_frames
                }
                # url = 'https://httpbin.org/post'
                # TODO connect to the model
                # response = requests.post(url, json=payload)
                frames = []
        else:
            pass # TODO
    os.remove(local_path)



@sio.on('send_prediction')
async def receive_and_send_model_prediction(sid, classes, confidences, bounding_boxes, orig_frame):
    await sio.emit("receive_prediction", {}) # TODO

# @sio.on('msg')
# async def client_side_receive_msg(sid, msg, student, alumni):
#     try:
#         chat_collection.update_one(
#             {"alumni": alumni},
#             {"$push": {
#                 "chat": {
#                     "time": datetime.datetime.now(),
#                     "text": msg,
#                     "sender": student}
#             }}
#         )
#         await sio.emit("msg", {"text": msg, "sender": student}, to=alumni)
#     except:
#         pass


# @sio.on('msgdelete')
# async def client_side_delete_msg(sid, msg, student, alumni):
#     try:
#         chat_collection.update_one(
#             {"alumni": alumni},
#             {"$pull": {
#                 "chat": {
#                     "text": msg,
#                     "sender": student
#                 }
#             }}
#         )
#         await sio.emit("msgdelete", {"text": msg, "sender": student}, to=alumni)
#     except:
#         pass


# @sio.on('event_updates')
# async def client_side_event_update(sid, alumni):
#     r = requests.get(url=f"{STATIC_API_URL}/event/history/{alumni}")
#     data = r.json()
#     await sio.emit("event_updates", data, to=alumni)