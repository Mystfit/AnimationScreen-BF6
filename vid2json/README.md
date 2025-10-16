# Video to JSON Converter

Convert videos to JSON format containing pixel data for each frame, with **RLE compression** and optional **color palette indexing** for significantly reduced file sizes. Includes a web-based player to visualize the output.

## Requirements

### Python Script
- Python 3.6+
- OpenCV (`cv2`)
- NumPy

Install dependencies:
```bash
pip install opencv-python numpy
```

## Features

### 🎨 Palette Indexing
When a color palette is provided, pixels are stored as palette indices instead of full RGB values, dramatically reducing file size.

### 🗜️ RLE Compression
Run-Length Encoding (RLE) compresses consecutive identical pixels, perfect for videos with solid color regions or simple graphics.

### 📦 Optimized Output Format
The new format includes:
- Embedded palette (when used)
- Width and height metadata
- RLE-compressed frame data
- Backward compatibility with old format

## Usage

### Converting Video to JSON

Basic usage:
```bash
python vid2json.py --video input.mp4 --width 320 --height 240 --frameskip 0
```

#### Arguments

- `--video` (required): Path to input video file
- `--width` (required): Target width in pixels for output
- `--height` (required): Target height in pixels for output
- `--frameskip` (optional, default: 0): Number of frames to skip
  - `0` = include every frame
  - `1` = include every other frame (halves frame rate)
  - `2` = include every third frame, etc.
- `--palette` (optional): Path to JSON file containing color palette

#### Examples

**Basic conversion** (640x360 resolution, all frames, with compression):
```bash
python vid2json.py --video myvideo.mp4 --width 640 --height 360 --frameskip 0
```

**Reduced frame rate** (include every 2nd frame):
```bash
python vid2json.py --video myvideo.mp4 --width 320 --height 240 --frameskip 1
```

**With color palette** (maximum compression - palette + RLE):
```bash
python vid2json.py --video myvideo.mp4 --width 160 --height 120 --frameskip 2 --palette monochrome.json
```

### Output

The script creates a JSON file with the same name as the input video:
- Input: `myvideo.mp4`
- Output: `myvideo.json`

#### New Optimized Format (with RLE compression)

```json
{
    "width": 320,
    "height": 240,
    "palette": [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0]
    ],
    "frames": [
        [[0, 150], [1, 200], [0, 76450]],
        [[1, 300], [0, 76500]]
    ]
}
```

Each frame is RLE-encoded as `[[value, count], ...]` where:
- With palette: `value` is a palette index, `count` is how many pixels
- Without palette: `value` is `[r, g, b]`, `count` is how many pixels

The player automatically detects and decodes both old and new formats.

## Color Palette Format

Create a JSON file with this structure:
```json
{
    "colours": [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0]
    ]
}
```

Each color is an RGB array with values from 0.0 to 1.0. The script will match each pixel to the closest color in the palette using Euclidean distance.

### Included Palettes

- **example-palette.json**: 11 colors (RGB primaries + grayscale)
- **monochrome.json**: 2 colors (black and white) - for maximum compression

## Compression Performance

The new format can achieve **massive file size reductions**:

| Configuration | Typical Compression |
|---------------|-------------------|
| No palette, RLE only | 20-40% smaller |
| With palette (16 colors) | 60-80% smaller |
| Monochrome + RLE | 90-95% smaller |

Best results with:
- Videos with solid color regions
- Cartoons and animations
- Low color count content
- Small palettes (2-16 colors)

## Web Player

Open `player.html` in a web browser to play back the generated JSON files.

### Features

- **File loading**: Click to select or drag-and-drop JSON files
- **Playback controls**: Play/Pause button
- **FPS control**: Adjust playback speed from 1-120 FPS
- **Frame counter**: Shows current frame and total frames
- **Format detection**: Automatically detects and displays format (RLE, Palette, etc.)
- **Auto-loop**: Automatically loops back to start when reaching the end
- **Backward compatible**: Supports both old and new JSON formats

### Usage

1. Open `player.html` in any modern web browser
2. Click "Choose File" and select your generated JSON file
3. The player will decode the format automatically
4. Use the Play button to start playback
5. Adjust FPS to control playback speed
6. Watch your video play back from the JSON data!

## How It Works

### Pixel Averaging

When the target resolution is smaller than the source video, the script averages pixels in regions:

- Source: 1920x1080 video
- Target: 960x540 output
- Each output pixel represents a 2x2 region in the source

The script calculates the average color of all pixels in each region.

### Color Matching

When a palette is provided:
1. Calculate the target pixel color (averaged from source region)
2. Compare against all palette colors using Euclidean distance in RGB space
3. Store the index of the closest matching color

### RLE Compression

Run-Length Encoding compresses frames by counting consecutive identical pixels:
- Original: `[0, 0, 0, 1, 1, 2, 2, 2, 2]`
- RLE: `[[0, 3], [1, 2], [2, 4]]`

This is especially effective for:
- Solid color backgrounds
- Simple graphics and animations
- Videos converted to small color palettes

### Frame Skipping

- `frameskip=0`: Process every frame
- `frameskip=1`: Process every 2nd frame (frames 0, 2, 4, 6...)
- `frameskip=2`: Process every 3rd frame (frames 0, 3, 6, 9...)
- `frameskip=N`: Process every (N+1)th frame

## Performance Tips

### For Smallest File Size
1. Use a small color palette (2-8 colors)
2. Reduce resolution significantly
3. Increase frameskip value
4. Choose videos with solid colors/simple content

### For Best Quality
1. Use higher resolution (but still downsampled)
2. Use larger palette (16-256 colors) or no palette
3. Lower frameskip (0 or 1)
4. Accept larger file sizes

### Optimal Settings for Different Content

**Black and white / monochrome videos:**
```bash
python vid2json.py --video input.mp4 --width 320 --height 240 --frameskip 1 --palette monochrome.json
```
Best compression, perfect for black and white content.

**Cartoons / Animations:**
```bash
python vid2json.py --video input.mp4 --width 480 --height 360 --frameskip 0 --palette example-palette.json
```
Good compression with acceptable quality.

**General video content:**
```bash
python vid2json.py --video input.mp4 --width 640 --height 360 --frameskip 1
```
RLE compression only, better quality but larger files.

## Example Workflow

1. Convert a video with maximum compression:
```bash
python vid2json.py --video badapple.mp4 --width 160 --height 120 --frameskip 1 --palette monochrome.json
```

2. Open `player.html` in your browser

3. Load `badapple.json` and watch it play!

4. Check file size - it should be dramatically smaller than the original!

## Troubleshooting

### "Module not found: cv2"
Install OpenCV: `pip install opencv-python`

### "Module not found: numpy"
Install NumPy: `pip install numpy`

### Large file sizes
- Use a color palette to enable palette indexing
- Reduce width and height
- Increase frameskip value
- Choose content that compresses well (solid colors, simple graphics)

### Slow processing
- Reduce target resolution
- Increase frameskip
- Process shorter video clips

### Player not working
- Ensure you're using a modern browser (Chrome, Firefox, Edge, Safari)
- Check browser console for errors (F12)
- Verify the JSON file is valid
- Player supports both old and new formats automatically

### Player shows "Decoding RLE frames..."
This is normal - the player decodes compressed frames on load. For very large files, this may take a few seconds.

## Technical Details

### Data Format
- RGB values normalized to 0.0-1.0 range in JSON
- Player converts these back to 0-255 for canvas rendering
- RLE format: `[[value, count], [value, count], ...]`
- Palette indices are integers (0 to palette_size-1)

### Compression Algorithm
- **RLE**: Simple run-length encoding on flattened pixel arrays
- **Palette**: Maps all colors to nearest palette color via Euclidean distance
- **Combined**: RLE on palette indices provides best compression

### Player Features
- Uses OpenCV for efficient video processing
- Canvas API for efficient frame rendering in browser
- RequestAnimationFrame for smooth playback timing
- Automatic format detection (old vs new format)
- Decodes all frames on load for smooth playback

## Comparison: Old vs New Format

### Old Format (Uncompressed)
```json
{
    "frames": [
        [
            [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], ...],
            [[0.5, 0.5, 0.5], [1.0, 0.0, 0.0], ...],
            ...
        ]
    ]
}
```
- Simple 3D array structure
- Full RGB for every pixel
- Larger file sizes

### New Format (Optimized)
```json
{
    "width": 320,
    "height": 240,
    "palette": [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
    "frames": [
        [[0, 500], [1, 300], [0, 75900]]
    ]
}
```
- Includes metadata
- RLE compression
- Palette indexing
- 10-100x smaller files possible

Both formats work with the player!

## License

This project is provided as-is for educational and personal use.
