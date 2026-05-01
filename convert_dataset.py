import cv2
import mediapipe as mp
import os
import csv

# 1. Initialize MediaPipe (Optimized for static images)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True, # Set to True because we are reading saved photos, not a video stream
    max_num_hands=1,
    min_detection_confidence=0.5
)

# 2. Setup Paths
dataset_path = 'F:/G12_major_project/Sign-Language-to-Text-master/dataset/asl_alphabet_train' # Change this to the folder where you extracted the downloaded dataset
csv_file = 'hand_landmarks.csv'

# 3. Create/Overwrite the CSV file
with open(csv_file, mode='w', newline='') as f:
    writer = csv.writer(f)
    headers = ['label']
    for i in range(21):
        headers.extend([f'x{i}', f'y{i}', f'z{i}'])
    writer.writerow(headers)

total_processed = 0
total_failed = 0

print(f"Starting conversion of images in '{dataset_path}' to coordinates...")

# 4. Loop through every folder (A-Z) and every image
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if file.endswith(('.jpg', '.jpeg', '.png')):
            # The label is the name of the folder (e.g., 'A')
            label = os.path.basename(root).upper()
            image_path = os.path.join(root, file)
            
            # Read image and convert to RGB for MediaPipe
            image = cv2.imread(image_path)
            if image is None:
                continue
                
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Extract landmarks
            results = hands.process(image_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    landmark_data = [label]
                    for lm in hand_landmarks.landmark:
                        landmark_data.extend([lm.x, lm.y, lm.z])
                        
                    # Save to CSV
                    with open(csv_file, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(landmark_data)
                
                total_processed += 1
                if total_processed % 500 == 0:
                    print(f"Processed {total_processed} images so far...")
            else:
                # MediaPipe couldn't find a hand in this specific photo
                total_failed += 1

print("\n--- Conversion Complete ---")
print(f"Successfully converted {total_processed} images into coordinates.")
print(f"Failed to find a hand in {total_failed} images (These were skipped to keep data clean).")
print(f"Your dataset is ready at {csv_file}")