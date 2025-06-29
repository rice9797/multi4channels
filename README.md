# Multi4Channels

Multi4Channels is a Python-based application that creates a 2x2 mosaic video stream from two, three, or four Channels DVR channels, streamed via RTP to Channels DVR for viewing as a single channel. The web interface allows users to select channels, manage favorites, and start/stop the stream.  

## Features
- **Mosaic Streaming**: Combines up to four Channels DVR streams into a 2x2 grid, output as a single MP4V video stream.  The output stream can be 2,3, or 4 stream combinations. 
- **Web UI**: Responsive interface for selecting channels, starting streams, and managing favorites, accessible on mobile or desktop.
- **Favorites**: Save and quickly select favorite channels from the Channels DVR M3U playlist.
- **Stream Switching**: Cleanly terminates existing streams before starting new ones to avoid conflicts, however you will need to restart the channel in CDVR. 
- **Auto-Stop**: Stops the stream after 6 minutes of inactivity on the target channel (configurable).


## Project Structure

1. Pick a channel number you want to use in Channels DVR for the new Multichannel stream. This Readme uses channel 240 as an example. 
2. Configure Channels DVR
•  Log into Channels DVR (e.g., http://192.168.1.152:8089).
•  Go to Settings > Sources and add a custom M3U source for the stream:
	•  Name: multi4channels (or any name).
	•  Choose Text in the drop down and copy paste changing channel number from 240 to what you want as the channel number.  Also change -docker.machine.ip- to the actual numbers. Customize text as you please. 

 ```bash
#EXTM3U
#EXTINF:0, channel-id="M4C" tvg-id="240" tvg-chno="240" tvc-guide-placeholders="7200" tvc-guide-title="Start a Stream At docker.machine.ip:9799..” tvc-guide-description="Visit Multi4Channels Web Page to Start a Stream (docker.machine.ip:9799).” tvc-guide-art="https://i.postimg.cc/xCy2v22X/IMG-3254.png"  tvg-logo="https://i.postimg.cc/xCy2v22X/IMG-3254.png" tvc-guide-stationid="" tvg-name="Multi4Channels" group-title="HD", M4C 
udp://0.0.0.0:4444
 ```
-*Note* There is no need to change udp://0.0.0.0:4444 in the text. udp://0.0.0.0:4444 is the proper url to receive the stream. 

Enter a starting channel number and select ignore channel number from m3u if you didn’t change in the text above. Leave the xmltv guide block blank and click save. 

3a. Use this compose or alternatively the docker run below(3b.). 
```bash
version: '3.9'
services:
  multi4channels:
    image: ghcr.io/rice9797/multi4channels:${TAG}
    container_name: multi4channels
    #devices:
      #- /dev/dri:/dev/dri
    ports:
      - ${HOST_RTP}:${RTP_PORT}
      - ${HOST_PORT}:${WEB_PAGE_PORT}
    environment:
      - CDVR_HOST=${CDVR_HOST} # Hostname/IP of Channels DVR server
      - CDVR_PORT=${CDVR_PORT} # Port of Channels DVR server
      - CDVR_CHNLNUM=${CDVR_CHNLNUM} # Channel number to monitor for activity
      - OUTPUT_FPS=${OUTPUT_FPS} # Output frame rate for the mosaic stream
      - RTP_HOST=${RTP_HOST} # Host for RTP stream output (same as CDVR_HOST in bridge mode)
      - RTP_PORT=${RTP_PORT} # Port for RTP stream output
      - WEB_PAGE_PORT=${WEB_PAGE_PORT} # Port for web UI
    volumes:
      - multi4channels:/app/data # Directory for favorites.json
    restart: unless-stopped
volumes:
  multi4channels:
    name: ${HOST_VOLUME}
```
Use with these sample enviornment variables:
```bash
TAG=v22 
HOST_RTP=4444 
RTP_PORT=4444
HOST_PORT=9799
WEB_PAGE_PORT=9799
CDVR_HOST=192.168.1.152
CDVR_PORT=8089
CDVR_CHNLNUM=240
OUTPUT_FPS=60
RTP_HOST=192.168.1.152
HOST_VOLUME=multi4channels_config

```

3b. If you prefer docker run use:

Pull the Docker Image

```bash
docker pull ghcr.io/rice9797/multi4channels:v22
```
Run the Container:

Run the container with environment variables:

``` bash 
docker run -d \
  --name multi4channels \
  -p 4444:4444 \
  -p 9799:9799 \
  -e CDVR_HOST=192.168.1.152 \
  -e CDVR_PORT=8089 \
  -e CDVR_CHNLNUM=240 \
  -e OUTPUT_FPS=60 \
  -e RTP_HOST=192.168.1.152 \
  -e RTP_PORT=4444 \
  -e WEB_PAGE_PORT=9799 \
  -v multi4channels_config:/app/data \
  --restart unless-stopped \
  ghcr.io/rice9797/multi4channels:v22
```

Environment Variables

IMPORTANT:   -e CDVR_CHNLNUM=240 \ is used to monitor the channels dvr api to watch for activity on the channel you choose to watch multiview on. When you stop watching the channel a 6 minute countdown begins and if the channel is not tuned again within 6 minutes the transcoding stops. USE this!!

CDVR_HOST= use the ip of your Channels dvr machine 

RTP_PORT= this is the stream output port and can be changed if 4444 is in use. 

OUTPUT_FPS= 25,30,50,60 should all work for choosing your desired frames per second. If you run in to pauses or hiccups in the stream reduce FPS. 

WEB_PAGE_PORT=9799 Change to desired port or if 9799 is in use. 

Notes:
•  If CDVR_CHNLNUM is unset, the inactivity check is disabled.

Usage

1. Access the Web UI
•  Open a browser on your device (e.g., iPhone or computer) and navigate to: docker.host.ip:9799
•  The UI displays four input boxes for channel numbers, a “Start Stream” button, and a favorites list.
2. Start a Stream
•  Enter up to four channel numbers (e.g., 6101, 6073, 6080, 6070) from Channels DVR’s M3U playlist.
•  Tap “Start Stream” and confirm the pop-up notification.
•  In Channels DVR, tune to channrl 240(or the channel you choose) to view the 2x2 mosaic stream.
•  Audio is sourced from the second channel (ch2).
3. Change Channels
•  Return to the web UI, enter new channel numbers, and tap “Start Stream.”
•  The existing stream stops, and the new stream starts within 5–10 seconds.
•  Channels DVR will require exiting the channel and restarting the channel. The channel doesn't seem to ever recover thus a back out and restart of the channel is required.
4. Manage Favorites
•  Click the hamburger menu (☰) and select “Available Channels.”
•  Add/remove favorites by clicking the heart icon (♥/♡) next to each channel.
•  Favorites appear in the main UI for quick selection.  Simply tap the channel from the favorites section and the next blank channel box will populate. This is a fast alternative to using the keyboard to enter channel numbers. 
•  Favorites are saved and persist across container restarts.
5. Stop the Stream
•  The stream stops automatically after 6 minutes if ch240 is not being watched (if CDVR_CHNLNUM=240). You can also use the web ui to stop a stream under the menu button. 


Limitations
 
•  Single Audio Source: Only ch2’s audio is included in the mosaic.

•  Stream Switching: Channels DVR will require reloading the channel inside the Channels app, it will not recover on its own. Simply backing out and selecting the channel again from the guide will load the newly started stream. 

Future Improvements
•  Hardware encoding. I would like to get intel QuickSync compatability for lower powered machines. I have not been able to get this to work in my many tests. 

Latest Improvements:
v22 tag:
- Updates for saving favorites to its own directory to persist restarts and play nicer with furure updates.
  
v2 tag:
- Added an End Current Stream option in the menu button.  Stream will still auto kill after channel is closed when using the enviornment variable but the kill button is there if you wabt to use it.
- Significantly reduced CPU consumption with code tweaks.
- Added logic to identify and use Intel QuickSync for hardware encoding if available. Currently un-tested and un-verified as working. 
- Added WEB_PAGE_PORT= variable to be able to change port number for the web ui page. 

License
MIT
	
Acknowledgments:

A Special Thank You to @https://github.com/bnhf for his help and contributions to this project and the many projects he supports for the Channels DVR community. 

•  Built with VLC for stream processing.
•  Powered by Flask for the web UI.
•  Designed for Channelsu DVR.
