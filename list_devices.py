"""
Utility script to list available audio devices.
Useful for finding the correct device name or index for voice injection.
"""
import sounddevice as sd

def list_audio_devices():
    print("Scanning audio devices...")
    print("-" * 90)
    
    try:
        devices = sd.query_devices()
        default_output = sd.default.device[1]
        
        print(f"{'IDX':<4} {'NAME':<40} {'CH':<4} {'API':<15} {'STATUS'}")
        print("-" * 90)
        
        # Keep track of seen names to avoid duplicates
        seen_names = set()
        
        # Collect relevant devices
        for i, device in enumerate(devices):
            channels = device['max_output_channels']
            
            # Filter: Only show devices that support output
            if channels <= 0:
                continue
            
            name = device['name']
            api_index = device['hostapi']
            host_api = sd.query_hostapis(api_index)['name']
            
            # Filter: Exclude WDM-KS and other less common APIs to reduce clutter
            if host_api == "Windows WDM-KS":
                continue

            # Filter: Exclude empty names
            if not name or name.strip() == "":
                continue
            
            # Filter: Deduplicate by name
            # If we've already seen this exact device name, skip it.
            # This simplifies the list for the user who just needs the name.
            if name in seen_names:
                continue
                
            seen_names.add(name)
                
            # Markers
            markers = []
            if i == default_output:
                markers.append("[DEFAULT]")
            
            marker_str = " ".join(markers)
            
            print(f"{i:<4} {name:<40} {channels:<4} {host_api:<15} {marker_str}")

        print("-" * 90)
        print("To configure the bot, set AUDIO_OUTPUT_DEVICE_NAME in your .env file")
        print("to the exact name (or a unique substring) of your target output device.")
        print("Example: AUDIO_OUTPUT_DEVICE_NAME=\"CABLE Input\"")
        
    except Exception as e:
        print(f"Error listing devices: {e}")

if __name__ == "__main__":
    list_audio_devices()
