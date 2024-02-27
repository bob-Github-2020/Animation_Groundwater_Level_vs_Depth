#!/usr/bin/python3

## 2-24-2024. Bob Wang
## Plot the animation: groundwater level vs. well depth, for all wells in HGSD Areas 1 & 2
## For view the generated videos, use: gifview -a Supplemental_animation.gif
## mpv Supplemental_animation.gif

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import glob
from matplotlib.animation import FuncAnimation, PillowWriter 
from matplotlib.animation import FFMpegWriter

# Define a function to process each line
def process_line(line):
    parts = line.strip().split()
    # Check if there are enough parts in the line to process
    if len(parts) > 1:
        well_id = parts[1]  # The second element is the Well ID
        well_depth = parts[-1]  # The last element is the Well Depth
        return well_id, well_depth
    else:
        return None, None  # Return None for both well_id and well_depth if the line is not as expected

# Initialize lists to store Well ID and Well Depth
well_ids = []
well_depths = []

## Open the summary file and process each line
#with open('List_HGSD_Zone1-2Wells.txt', 'r') as file:
with open('List_HGSD_Area1and2_Wells_Selected.txt', 'r') as file:
    next(file)  # Skip the header line if there is one
    for line in file:
        well_id, well_depth = process_line(line)
        if well_id is not None and well_depth is not None:
            well_ids.append(well_id)
            well_depths.append(well_depth)

# Create a DataFrame from the Well ID and Well Depth lists
summary_df = pd.DataFrame({
    'WellID': well_ids,
    'WellDepth': well_depths
})

# Ensure that Well Depth is numeric, converting non-numeric values to NaN
summary_df['WellDepth'] = pd.to_numeric(summary_df['WellDepth'], errors='coerce')

# Drop any rows that have NaN for WellDepth as we can't use these for the animation
summary_df.dropna(subset=['WellDepth'], inplace=True)

# Convert WellDepth to a float, if it's not already
summary_df['WellDepth'] = summary_df['WellDepth'].astype(float)

# Create a dictionary with Well ID as keys and Well Depth as values
well_depths_dict = summary_df.set_index('WellID')['WellDepth'].to_dict()

# Check the first few items of the dictionary to ensure it's correct
print(list(well_depths_dict.items())[:5])


#****************************************
# Function to read groundwater level data
  
def read_groundwater_data(filename, well_depths_dict):
    # Extract the well ID from the filename
    well_id = filename.split('_')[0]
    # Read the data file
    data_df = pd.read_csv(filename, delim_whitespace=True, usecols=[0, 2], header=0)
    data_df.columns = ['Year', 'GroundwaterLevel']
    # Add well ID and well depth to the DataFrame
    data_df['WellID'] = well_id
    data_df['WellDepth'] = well_depths_dict.get(well_id, float('nan'))
    return data_df
  

# Get all data filenames
data_filenames = glob.glob('*_orig_dyear.col')

# Make sure to pass the well_depths_dict to this function call
all_data = pd.concat([read_groundwater_data(f, well_depths_dict) for f in data_filenames])

# Sort the DataFrame based on well depth
all_data_sorted = all_data.sort_values(by='WellDepth')


# Set up the figure for animation
fig, ax = plt.subplots()

# Set the limits of the axes before the animation starts
ax.set_xlim(1920, 2025)  # Set X-axis limits
ax.set_ylim(-180, 30)    # Set Y-axis limits

# Set labels for the axes
ax.set_xlabel('Year')
ax.set_ylabel('Groundwater Level (m, NAVD88)')

# Initialize a container to hold all the plotted lines
plotted_data = []

# Add a variable to keep track of the animation's state
is_paused = False  # Start with the animation not paused

# Function to update the scatter plot for each frame
def update(frame_number):
    global is_paused
    if is_paused:
       return plotted_data
    
    # Get the current well data
    current_data = all_data_sorted[all_data_sorted['WellDepth'] == all_data_sorted['WellDepth'].unique()[frame_number]]
    
    
    # Plot the new time series and add it to the list of plotted data
    new_scat = ax.scatter(current_data['Year'], current_data['GroundwaterLevel'], s=3)
    plotted_data.append(new_scat)
    
    ax.grid(which='both', linestyle='--', linewidth=0.5)
    
    # Get the well ID from the current data
    well_id = current_data['WellID'].values[0]
    current_depth = current_data['WellDepth'].values[0]
    
    # Update the title to include the well ID and the current well depth
    ax.set_title(f'HGSD Areas 1&2 Wells: ID {well_id} - Depth: {current_depth * 0.3048:.1f}m', fontsize=10)
    
    # Export each frame as a PNG file
      #plt.savefig(f'{well_id}_frame_{frame_number}.png')
     
    return plotted_data
    
 
# Function to toggle the pause state
def onClick(event):
    global is_paused
    is_paused = not is_paused

# Connect the onClick function to the figure
fig.canvas.mpl_connect('button_press_event', onClick)


# Create the animation by accumulating the frames instead of replacing them
ani = animation.FuncAnimation(fig, update, frames=len(all_data_sorted['WellDepth'].unique()), interval=450, repeat=False, blit=False)



## Set up the writer - you can choose between different writers like 'ffmpeg' or 'pillow'
## PillowWriter creates a .gif file, which is generally easier to handle
writer = PillowWriter(fps=15)  # or use FFMpegWriter for more options

## Save the animation
ani.save('Supplemental_animation.gif', writer=writer)

# If using 'ffmpeg' and want to save as .mp4, use:
writer = FFMpegWriter(fps=20, metadata=dict(artist='Me'), bitrate=1800)
ani.save('Supplemental_animation.mp4', writer=writer)

## Display the animation
#plt.show()


def plot_well_data(well_data):
    for well_id, data in well_data.groupby('WellID'):
        fig, ax = plt.subplots()
        # ax.plot(data['Year'], data['GroundwaterLevel'], marker='o', linestyle='-', color='blue')
        ax.plot(data['Year'], data['GroundwaterLevel'], marker='o', linestyle='',color='blue')
        
        depth = well_depths_dict[well_id]
        ax.set_title(f'Well ID {well_id} at Depth {depth * 0.3048:.1f}m')
        ax.set_xlabel('Year')
        ax.set_ylabel('Groundwater Level (m)')
        ax.grid(which='both', linestyle='--', linewidth=0.5)
        ax.set_xlim(1920, 2025)
        ax.set_ylim(-150, 30)
        
        plt.savefig(f'{well_id}_{int(depth* 0.3048)}m.png')
        
        plt.close()

# Then call the function with the sorted data
plot_well_data(all_data_sorted)



# The plt.show() is no longer needed as we are saving figures directly to files.


