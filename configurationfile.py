#!/usr/bin/env python3

#utility to work with config files such as "config.ini" for TG16 games, and "config" for MasterSystem/Genesis/some Arcade games

def getConfiguration(file, key):
    file.seek(0)
    keyPart = key.encode('ascii', 'strict') + b'='
    for line in file:
        if line.startswith(keyPart):
            return line[len(keyPart):].strip(b'/\\\"\0\r\n').decode('ascii','strict')
    return None
