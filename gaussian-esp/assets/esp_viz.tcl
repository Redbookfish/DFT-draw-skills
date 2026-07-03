# ESP Visualization Script for VMD
# Usage: In VMD Tk Console, run: source esp_viz.tcl
# Modify the variables below to match your files

set basename "molecule"

# Clear scene
mol delete all

# Load structure and ESP cube
mol new ${basename}.fchk type gaussian
mol addfile ${basename}_ESP.cub type gaussian

# Remove default representation
mol delrep 0 top

# --- Representation 1: Ball-and-stick for atoms ---
mol representation Licorice 0.15 12 12
mol color Name
mol material Opaque
mol addrep top

# --- Representation 2: ESP-colored isosurface ---
mol representation Isosurface 0.001 0 0 0 1 1
mol color Volume 0
mol material AOShiny
mol addrep top

# Color scale: negative (red) → neutral (white) → positive (blue)
# Adjust range based on your system
mol scaleminmax top 0 -0.05 0.05

# Adjust color scheme to RWB
# In VMD GUI: Graphics → Colors → Color Scale → RWB

# Presentation settings
color Display Background white
axes location Off
display depthcue off
display projection Orthographic

# Reset view and rotate
display resetview
rotate x by 25
rotate y by 45

# Scale to fit
scale by 1.2

# Uncomment to render:
# render TachyonInternal ${basename}_esp.tga
# render Snapshot ${basename}_esp.png
