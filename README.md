# Automatic Media Classifier

## Synopsis

Automatic Media Classifier will classify and sort TV shows and Movies automatically. After classifying and sorting a Movie or TV show, Automatic Media Classifier can send users a XMPP message indicating that their media is ready to watch. I personally use Plex 


## Prerequisities/Installation

What things you need to install the software and how to install them
- Python 2.7
- Configuration file
    - A configuration file MUST be filled out. An explanation and example config file can be found at ```config_explanation``` and ```config_example``` respectively. 
- pyxmpp2 **[Optional]**
    -  Used to send XMPP messages to users upon successful parse of media. 
    - ``` sudo easy_install pyxmpp2 ```
- [showRSS](http://new.showrss.info) **[Optional]**
    - Create a showRSS account, sign up for TV shows, and generate a personal RSS feed.
- [uTorrnet](http://www.utorrent.com/) **[Optional]**
    - After installing utorrent there are a few settings which need to be set:
    #### Linux/OS X
    - Settings -> Directories -> Put new downloads in: Fill this in with an absolute path
    - Settings -> Directories -> Move completed downloads to: Fill this in with an absolute path
    - Settings -> Advanced -> Run Program -> Run this program when a torrent finishes: ```/usr/bin/python2.7 .../media_parser.py```
    - Adding an RSS feed: Click the add RSS button on the main screen
        - Fill in your showRSS link for 'Feed:'
        - Under 'Subscription' Choose 'Automatically download all items published in feed'

## Running the program
- ```media_parser.py``` must be edited to tell the program where to find the configuration file. This option is found on lines 249-254. Simple edit the string that corresponds to the operatng system you are running. 
    ### Automatically
    - To automate the entire process, all of the prerequisities listed above are required.
    - Please see the settings above for uTorrent. Once those settings are set, any torrent that is downloaded will be automatically parsed. 

    ### Manually
    - To run the program: ```/usr/bin/python2.7 .../media_parser.py```

## Integration
- Automatic Media Classifier works very well in conunction with [Plex Media Server](https://plex.tv/)

## API Reference
- [pyxmpp2](https://github.com/Jajcus/pyxmpp2)

## Authors

* **Tyler Haugen-Stanley**

## License

- Please see ```License.md```


