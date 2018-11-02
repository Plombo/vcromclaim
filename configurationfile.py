#utility to work with config files such as "config.ini" for TG16 games, and "config" for MasterSystem/Genesis/some Arcade games

def getConfiguration(file, key):
    file.seek(0)
    for line in file:
        if line.startswith(key + '='):
            return line[len(key + '='):].strip('/\\\"\0\r\n')
    return None
