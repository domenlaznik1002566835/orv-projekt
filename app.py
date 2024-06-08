from flask import Flask, request, jsonify, send_from_directory
import requests
from werkzeug.utils import secure_filename
import os
import cv2
from compare import compare_images  

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'project-rai-backend', 'uploads'))
app.config['FRAME_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frames'))

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FRAME_FOLDER'], exist_ok=True)

def extract_frames(video_path, num_frames=3):
    print(f"Extracting frames from video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")
    frame_interval = total_frames // num_frames
    frames = []

    for i in range(num_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
        ret, frame = cap.read()
        if ret:
            frame_filename = os.path.join(app.config['FRAME_FOLDER'], f'frame_{i}.jpg')
            cv2.imwrite(frame_filename, frame)
            frames.append(frame_filename)
            print(f"Extracted frame {i}: {frame_filename}")
        else:
            print(f"Failed to extract frame {i}")
    
    cap.release()
    return frames

@app.route('/process_video', methods=['POST'])
def process_video():
    file_path = request.json.get('file_path')
    file_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(file_path)))
    print(f"Received request to process video. File path: {file_path}")

    if not file_path or not os.path.exists(file_path):
        print(f"Invalid file path: {file_path}")
        return jsonify({'error': 'File path is invalid or does not exist'}), 400

    print(f"Processing video file at path: {file_path}")

    # Extract frames from the video
    frames = extract_frames(file_path)
    if not frames:
        print("Failed to extract frames from video")
        return jsonify({'error': 'Failed to extract frames from video'}), 500

    print(f"Extracted frames: {frames}")

    # Call compare_images function with extracted frames
    verification_result = compare_images(frames)  # Pass the list of image paths
    print(f"Verification result from compare_images: {verification_result}")

    # Comment out the frame deletion part for debugging
    # for frame in frames:
    #     try:
    #         os.remove(frame)
    #         print(f"Removed frame: {frame}")
    #     except Exception as e:
    #         print(f"Error removing frame {frame}: {e}")

    if verification_result == 0:
        print("No match found")
        return jsonify({'success': False, 'identity': 0}), 200
    else:
        print(f"Match found: Identity {verification_result}")
        return jsonify({'success': True, 'identity': verification_result}), 200

@app.route('/get_video/<filename>', methods=['GET'])
def get_video(filename):
    print(f"Received request to get video: {filename}")
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return jsonify({'error': 'File not found'}), 404

@app.route('/send_notification', methods=['POST'])
def send_notification():
    data = request.json
    registration_id = data.get('registration_id')
    title = data.get('title')
    message = data.get('message')
    print(f"Sending notification to {registration_id} with title '{title}' and message '{message}'")

    try:
        response = requests.post('http://localhost:3001/send-notification', json={
            'userId': registration_id,
            'title': title,
            'message': message
        })
        if response.status_code == 200:
            print("Notification sent successfully")
            return jsonify({'message': 'Notification sent successfully'}), 200
        else:
            print(f"Failed to send notification. Status code: {response.status_code}")
            return jsonify({'error': 'Failed to send notification'}), response.status_code
    except Exception as e:
        print(f"Error sending notification: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/list_uploads', methods=['GET'])
def list_uploads():
    print("Received request to list files in 'uploads' folder")
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        print(f"Files in 'uploads' folder: {files}")
        return jsonify({'files': files}), 200
    except Exception as e:
        print(f"Error listing files in 'uploads' folder: {e}")
        return jsonify({'error': str(e)}), 500

def print_uploads_on_startup():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        print("Files in 'uploads' folder at startup:")
        for file in files:
            print(file)
    except Exception as e:
        print(f"Error listing files in 'uploads' folder: {e}")

if __name__ == '__main__':
    print_uploads_on_startup()  
    app.run(debug=True)
