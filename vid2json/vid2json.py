import cv2
import numpy as np
import argparse
import math
import json
import sys
import os

def load_palette(palette_path):
    """Load color palette from JSON file."""
    with open(palette_path, 'r') as f:
        palette_data = json.load(f)
    return np.array(palette_data['colours'], dtype=np.float32)

def find_closest_color_index(color, palette):
    """Find the index of the closest color in the palette using Euclidean distance."""
    color = np.array(color, dtype=np.float32)
    distances = np.sqrt(np.sum((palette - color) ** 2, axis=1))
    closest_idx = np.argmin(distances)
    return int(closest_idx)

def average_region(frame, x_start, y_start, x_end, y_end):
    """Average pixels in a region and return normalized RGB."""
    region = frame[y_start:y_end, x_start:x_end]
    avg_color = np.mean(region, axis=(0, 1))
    # Normalize to 0.0-1.0 range (OpenCV uses BGR, convert to RGB)
    return [float(avg_color[2]) / 255.0, float(avg_color[1]) / 255.0, float(avg_color[0]) / 255.0]

def rle_encode_frame(frame_data, use_palette=False):
    """
    Run-length encode a frame to compress consecutive identical values.
    
    Args:
        frame_data: Flattened list of pixel values (either color indices or RGB arrays)
        use_palette: If True, frame_data contains indices; if False, contains RGB arrays
    
    Returns:
        Flat array alternating between value and count: [value1, count1, value2, count2, ...]
    """
    if len(frame_data) == 0:
        return []
    
    encoded = []
    current_value = frame_data[0]
    count = 1
    
    for i in range(1, len(frame_data)):
        if use_palette:
            # Compare indices directly
            is_same = frame_data[i] == current_value
        else:
            # Compare RGB arrays
            is_same = (frame_data[i][0] == current_value[0] and 
                      frame_data[i][1] == current_value[1] and 
                      frame_data[i][2] == current_value[2])
        
        if is_same:
            count += 1
        else:
            # Append value and count as separate elements in flat array
            if use_palette:
                encoded.append(current_value)
            else:
                encoded.extend(current_value)
            encoded.append(count)
            current_value = frame_data[i]
            count = 1
    
    # Add the last run
    if use_palette:
        encoded.append(current_value)
    else:
        encoded.extend(current_value)
    encoded.append(count)
    
    return encoded

def process_video(video_path, target_width, target_height, frameskip, palette=None, total_exported_frames=0):
    """Process video and convert to optimized JSON format with RLE compression."""
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        sys.exit(1)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Video properties:")
    print(f"  Resolution: {video_width}x{video_height}")
    print(f"  FPS: {fps}")
    print(f"  Total frames: {total_frames}")
    print(f"  Target resolution: {target_width}x{target_height}")
    print(f"  Frame skip: {frameskip}")
    print(f"  Total frames to save {total_exported_frames}")
    if palette is not None:
        print(f"  Using palette with {len(palette)} colors")
    print()
    
    # Calculate scaling factors
    x_scale = video_width / target_width
    y_scale = video_height / target_height
    
    frames_data = []
    frame_count = 0
    processed_count = 0
    use_palette = palette is not None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if total_exported_frames > 0 and processed_count >= total_exported_frames:
            break
        
        # Check if we should process this frame based on frameskip
        if frame_count % (frameskip + 1) == 0:
            # Create flat list of pixel values for this frame
            pixel_values = []
            
            for y in range(target_height):
                for x in range(target_width):
                    # Calculate source region
                    x_start = int(x * x_scale)
                    y_start = int(y * y_scale)
                    x_end = int((x + 1) * x_scale)
                    y_end = int((y + 1) * y_scale)
                    
                    # Ensure we don't go out of bounds
                    x_end = min(x_end, video_width)
                    y_end = min(y_end, video_height)
                    
                    # Average the region
                    color = average_region(frame, x_start, y_start, x_end, y_end)
                    
                    # Store as palette index or full color
                    if use_palette:
                        color_index = find_closest_color_index(color, palette)
                        pixel_values.append(color_index)
                    else:
                        pixel_values.append(color)
            
            # Apply RLE compression
            compressed_frame = rle_encode_frame(pixel_values, use_palette)
            frames_data += compressed_frame
            processed_count += 1
            
            # Display progress
            progress = (frame_count + 1) / total_frames * 100
            print(f"\rProcessing: {progress:.1f}% (frame {frame_count + 1}/{total_frames})(Saved frames {processed_count})", end='', flush=True)
        
        frame_count += 1
    
    print()  # New line after progress
    cap.release()
    
    print(f"Processed {processed_count} frames")
    
    # Build output JSON structure
    if use_palette:
        # json_data = {
        #     "width": target_width,
        #     "height": target_height,
        #     "palette": palette.tolist(),
        #     "frames": frames_data
        # }
        json_data = frames_data;
    else:
        json_data = {
            "width": target_width,
            "height": target_height,
            "frames": frames_data
        }
    
    return json_data

def main():
    parser = argparse.ArgumentParser(description='Convert video to JSON pixel data with RLE compression')
    parser.add_argument('--video', required=True, help='Input video file path')
    parser.add_argument('--width', type=int, required=True, help='Target width in pixels')
    parser.add_argument('--height', type=int, required=True, help='Target height in pixels')
    parser.add_argument('--frameskip', type=int, default=0, help='Number of frames to skip (0 = include all frames)')
    parser.add_argument('--palette', help='Optional JSON file containing color palette')
    parser.add_argument('--buckets', type=int, default=1, help='Split frame data into fixed-size buckets')
    parser.add_argument('--totalframes', type=int, default=0, help='Max number of frames to save')
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.width <= 0 or args.height <= 0:
        print("Error: Width and height must be positive integers")
        sys.exit(1)
    
    if args.frameskip < 0:
        print("Error: Frameskip must be non-negative")
        sys.exit(1)
    
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)
    
    # Load palette if provided
    palette = None
    if args.palette:
        if not os.path.exists(args.palette):
            print(f"Error: Palette file not found: {args.palette}")
            sys.exit(1)
        print(f"Loading palette from: {args.palette}")
        palette = load_palette(args.palette)
        print(f"Loaded {len(palette)} colors from palette")
        print()
    
    # Process video
    print("Starting video processing...")
    json_data = process_video(args.video, args.width, args.height, args.frameskip, palette, args.totalframes)
    formatted_json_frames = {}
    total_data_size = len(json_data)
    bucket_length = math.floor(total_data_size / args.buckets)
    print(f"Bucket size:{bucket_length}")
    bucket_idx = 0
    current_bucket = []

    for idx, val in enumerate(json_data):
        if f"f{str(bucket_idx)}" not in formatted_json_frames:
            formatted_json_frames[f"f{str(bucket_idx)}"] = ""
        current_bucket.append(val)
        if(idx % bucket_length == 0) and idx > 0:
            formatted_json_frames[f"f{str(bucket_idx)}"] = ",".join([str(v) for v in current_bucket])
            current_bucket.clear()
            bucket_idx += 1
    
    # Create output filename
    base_name = os.path.splitext(args.video)[0]
    output_path = f"{base_name}.json"
    
    # Write JSON output (minified - no unnecessary whitespace)
    print(f"Writing output to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(formatted_json_frames, f, separators=(',', ':'))
    
    # Calculate and display file size
    file_size = os.path.getsize(output_path)
    if file_size < 1024:
        size_str = f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    
    print(f"Output file size: {size_str}")
    print("Done!")

if __name__ == "__main__":
    main()
