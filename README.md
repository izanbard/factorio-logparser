# Factorio Log Parser
A crude log parser for Factorio console log.

The script will output a json file containing the connected users and some of their actions throughout the server lifetime.

## Output (JSON)
A json file which lists users that appear in the console log:

Example:
 ```JSON
{
    "generated": "2018-07-01 20:31:58",
    "users": {
        "Stark": {
            "last_seen": "2018-07-01 14:22:13",
            "online": false
        },
        "Banner": {
            "last_chat": "Don't make me angry!",
            "last_seen": "2018-07-01 19:57:19",
            "online": true
        },
        "Odinson": {
            "kicks": [
                "2018-07-01 17:40:29",
                "Banner",
                "Being too puny"
            ],
            "last_chat": "Heimdall, I need more plate.",
            "last_seen": "2018-07-01 20:29:36",
            "online": false
        },
        "ClintB": {
            "bans": [
                "2018-07-01 16:25:11",
                "RedBack",
                "Inappropriate language"
            ],
            "last_chat": "Where wer you hiding that gun?",
            "last_seen": "2018-07-01 16:25:11",
            "last_command": "/c Some Command",
            "online": false
        }
    }
}
```
## Requirements
- Python 3.5+
- Factorio 0.16+

## Setup and Use
- clone the repo
```bash
$ git clone https://github.com/izanbard/factorio-logparser.git
```
- install requirements
```bash
$ pip install -r requirments.txt 
```
- run factorio server with console.log
```bash
$ /path/to/factorio --config /path/to/config.ini --start-server-load-latest --server-settings /path/to/server-settings.json --console-log /path/for/console.log
```
- run this python script
```bash
$ python /path/to/factorio-logparser.py -o ./output.json -f 60 /path/for/console.log
```

### Options
```
-o <<file>> #set out put file
-f <<number>> #set update frequency in seconds
```

## Acknowledgments
This is version of the log parser is based on the design of [https://github.com/Bisa/factorio-logparser](https://github.com/Bisa/factorio-logparser) coupled with the regex schema from [https://github.com/mickael9/factoirc](https://github.com/mickael9/factoirc).

