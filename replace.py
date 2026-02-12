import json
import os

# ----------------------------------------------------------------------------------
# CONFIGURATION: PATHS
# ----------------------------------------------------------------------------------
BASE_DIR = "./minecraft/json/block"
OUTPUT_DIR = "./minecraft/new"
INPUT_SIDE = os.path.join(BASE_DIR, "crimson_stem.json")
INPUT_TOP = os.path.join(BASE_DIR, "crimson_stem_top.json")

OUTPUT_SIDE = os.path.join(OUTPUT_DIR, "charred_stem.json")
OUTPUT_TOP = os.path.join(OUTPUT_DIR, "charred_stem_top.json")

# ----------------------------------------------------------------------------------
# COMPREHENSIVE COLOR MAPPING
# Crimson (Purple/Red) -> Charred (Black/Ash/Magma)
# ----------------------------------------------------------------------------------
COLOR_MAP = {
    # --- OUTER BARK (Dark Purples -> Deep Charcoal/Blacks) ---
    "#442131ff": "#111111ff",  # Base dark bark
    "#4b2737ff": "#1a1a1aff",  # Mid bark
    "#562c3eff": "#222222ff",  # Light bark highlight
    
    # --- SIDE ANIMATION VEINS (Pulsing Reds -> Magma Gradient) ---
    "#521810ff": "#050505ff",  # Vein background (almost black/void)
    "#7b0000ff": "#802200ff",  # Dim ember (Dark Orange)
    "#890f0fff": "#a63c00ff",  # Mid ember
    "#961515ff": "#d45500ff",  # Bright ember
    "#b12727ff": "#ff7700ff",  # Hot spot (Brightest Orange)

    # --- TOP TEXTURE SPECIFICS ---
    # The top texture uses specific reds for the center cracks
    "#ac2020ff": "#ff9000ff",  # Center core hot magma
    "#941818ff": "#c04000ff",  # Center core cooling magma

    # --- TOP RINGS (Pinks/Purples -> Ash Greys) ---
    # The "wood rings" on top are pink in crimson wood. We make them ash grey.
    "#863e5aff": "#3a3a3aff",  # Ring Light Grey
    "#7e3a56ff": "#303030ff",  # Ring Mid Grey
    "#924160ff": "#454545ff",  # Ring Highlight (Lighter Ash)
    "#5c3042ff": "#252525ff",  # Ring Shadow (Dark Ash)
    "#6a344bff": "#2d2d2dff",  # Ring Darker Grey
}

def process_file(input_path, output_path):
    print(f"Processing: {input_path}...")
    
    if not os.path.exists(input_path):
        print(f"Error: File not found at {input_path}")
        return

    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Validate structure
        if "pixels" not in data:
            print(f"Error: 'pixels' array not found in {input_path}")
            return

        new_pixels = []
        replaced_count = 0
        unknown_colors = set()

        for pixel in data["pixels"]:
            # Normalize to lowercase just in case
            pixel_lower = pixel.lower()
            
            if pixel_lower in COLOR_MAP:
                new_pixels.append(COLOR_MAP[pixel_lower])
                replaced_count += 1
            else:
                # Keep original if not found in map
                new_pixels.append(pixel)
                # Ignore transparent pixels usually, but track others for debugging
                if pixel_lower != "#00000000":
                    unknown_colors.add(pixel_lower)

        # Update data
        data["pixels"] = new_pixels

        # Save to new file
        with open(output_path, 'w') as f:
            json.dump(data, f) # Minified output to save space
            
        print(f"Success! Saved to {output_path}")
        print(f"  - Replaced {replaced_count} pixels.")
        if unknown_colors:
            print(f"  - Warning: {len(unknown_colors)} colors were not mapped and kept original: {unknown_colors}")

    except Exception as e:
        print(f"An error occurred processing {input_path}: {e}")

if __name__ == "__main__":
    # Ensure directory exists just in case
    if not os.path.exists(BASE_DIR):
        print(f"Warning: Directory {BASE_DIR} does not exist. Please check your paths.")
    else:
        process_file(INPUT_SIDE, OUTPUT_SIDE)
        process_file(INPUT_TOP, OUTPUT_TOP)