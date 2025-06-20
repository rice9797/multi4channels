# Multi4Channels

Multi4Channels is a Python-based application that creates a 2x2 mosaic video stream from up to four Channels DVR channels, streamed via RTP to Channels DVR for viewing as a single channel (e.g., `ch199`). The web interface allows users to select channels, manage favorites, and start/stop the stream. The project runs in a Docker container using host networking for seamless integration with Channels DVR on the same machine.

## Features
- **Mosaic Streaming**: Combines up to four Channels DVR streams into a 2x2 grid, output as a single H.264 video stream.
- **Web UI**: Responsive interface for selecting channels, starting streams, and managing favorites, accessible on mobile or desktop.
- **Favorites**: Save and quickly select favorite channels from the Channels DVR M3U playlist.
- **Graceful Stream Switching**: Cleanly terminates existing streams before starting new ones to avoid conflicts.
- **Host Mode**: Runs in Docker with `--network host` for direct communication with Channels DVR.
- **Auto-Stop**: Stops the stream after 6 minutes of inactivity on the target channel (configurable).

## Prerequisites
- **Docker**: Installed on the host machine (tested with Docker 20.10+).
- **Channels DVR**: Running on the same host (default: `http://192.168.1.152:8089`).
- **VLC**: Included in the Docker image for stream processing.
- **Network**: Host machine and Channels DVR must be on the same network (e.g., `192.168.1.x`).
- **Background Image**: `app/photos/bg.jpg` (included) for the mosaic background.

## Project Structure


2. Configure Channels DVR
•  Log into Channels DVR (e.g., http://192.168.1.152:8089).
•  Go to Settings > Sources and add a custom M3U source for the mosaic stream:
	•  Name: multi4channels (or any name, e.g., for ch199).
	•  Choose Text in the drop down and copy paste changing channel number from 240 to what you want as the channel number.  Also change -docker.machine.ip- to the actual numbers. 

 ```bash
#EXTM3U
#EXTINF:0, channel-id="M4C" tvg-id="240" tvg-chno="240" tvc-guide-placeholders="7200" tvc-guide-title="Start a Stream At docker.machine.ip:9799..” tvc-guide-description="Visit Multi4Channels Web Page to Start a Stream (docker.machine.ip:9799).” tvc-guide-art="https://i.postimg.cc/xCy2v22X/IMG-3254.png"  tvg-logo="https://i.postimg.cc/xCy2v22X/IMG-3254.png" tvc-guide-stationid="" tvg-name="Multi4Channels" group-title="HD", M4C 
udp://127.0.0.1:4444
 ```
Enter a starting channel number and select ignore channel number from m3u if you didn’t change in the text above. Leave the xmltv guide block blank and click save. 

3. Create a Volume for Favorites 
To persist favorite channels:

```bash
mkdir -p ~/multi4channels/app
touch ~/multi4channels/app/favorites.json
chmod 666 ~/multi4channels/app/favorites.json
```

Pull the Docker Image

```bash
docker pull ghcr.io/rice9797/multi4channels:v1
```

4. Run the Container
Run the container in host mode with environment variables:

``` bash 
docker run -d --name multi4channels --restart unless-stopped --network host \
  -e CDVR_HOST=192.168.1.152 \
  -e CDVR_PORT=8089 \
  -e CDVR_CHNLNUM=240 \
  -e OUTPUT_FPS=60 \
  -e RTP_HOST=127.0.0.1 \
  -e RTP_PORT=4444 \
  -v ~/multi4channels/app/favorites.json:/app/favorites.json \
  ghcr.io/rice9797/multi4channels:v1
```

Environment Variables:

IMPORTANT:   -e CDVR_CHNLNUM=240 \ is used to monitor the channels dvr api to watch for activity in the channels you choose to watch multiview on. When you stop watching the channel a 6 minute countdown begins and if the channel is not tuned again within 6 minutes the transcoding stops. USE this as there is currently no other way to stop the stream. 

CDVR_HOST= use the ip of your Channels dvr machine 

RTP_PORT= this is the stream output port and can be changed if 4444 is in use. 

OUTPUT_FPS= 25,30,50,60 should all work for choosing your desired frames per second. 

Notes:
•  --network host: Ensures the container can communicate with Channels DVR on 127.0.0.1:4444.
•  -v $(pwd)/app:/app: Mounts the app directory for persistent changes and favorites.
•  If CDVR_CHNLNUM is unset, the inactivity check is disabled.
Usage
1. Access the Web UI
•  Open a browser on your device (e.g., iPhone or computer) and navigate to: docker.host.ip:9799
•  The UI displays four input boxes for channel numbers, a “Start Stream” button, and a favorites list.
2. Start a Stream
•  Enter up to four channel numbers (e.g., 6101, 6073, 6080, 6070) from Channels DVR’s M3U playlist.
•  Tap “Start Stream” and confirm the pop-up notification.
•  In Channels DVR, tune to ch199 (Multi4x) to view the 2x2 mosaic stream.
•  Audio is sourced from the second channel (ch2).
3. Change Channels
•  Return to the web UI, enter new channel numbers, and tap “Start Stream.”
•  The existing stream stops, and the new stream starts within 5–10 seconds.
•  Channels DVR will require exiting the channel and restarting the channel. The channel doesn't seem to ever recover thus a back out and restart of the channel is required.
4. Manage Favorites
•  Click the hamburger menu (☰) and select “Available Channels.”
•  Add/remove favorites by clicking the heart icon (♥/♡) next to each channel.
•  Favorites appear in the main UI for quick selection.
•  Favorites are saved to /app/favorites.json and persist across container restarts.
5. Stop the Stream
•  The stream stops automatically after 6 minutes if ch199 is not being watched (if CDVR_CHNLNUM=199).


Limitations
•  Host Mode Only: Currently configured for --network host. Bridge mode may require additional network configuration and code changes. 
•  Channels DVR Dependency: Requires Channels DVR on the same host with accessible streams.
•  Single Audio Source: Only ch2’s audio is included in the mosaic.
•  Stream Switching: Channels DVR will require reloading the channel, it will not recover on its own.

Future Improvements
•  Support bridge mode.  I would love to figure out how to run this in bridge mode but the stream output breaks everytime I try.  Can you help?

License
MIT
	
Acknowledgments
•  Built with VLC for stream processing.
•  Powered by Flask for the web UI.
•  Designed for Channels DVR.


