import os, re, time, threading

def filename(self):
    name = self.nick + '-' + self.config.host + '.reminders.db'
    return os.path.join(os.path.expanduser('~/.ircbot'), name)

def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = open(name, 'rb')
        for line in f:
            unixtime, channel, nick, message = line.split('\t')
            message = message.rstrip('\n')
            t = int(unixtime)
            reminder = (channel, nick, message)
            try:
                data[t].append(reminder)
            except KeyError:
                data[t] = [reminder]
        f.close()
    return data

def dump_database(name, data):
    f = open(name, 'wb')
    for unixtime, reminders in data.iteritems():
        for channel, nick, message in reminders:
            f.write('%s\t%s\t%s\t%s\n' % (unixtime, channel, nick, message))
    f.close()

def setup(ircbot):
    ircbot.rfn = filename(ircbot)
    ircbot.rdb = load_database(ircbot.rfn)

    def monitor(ircbot):
        time.sleep(5)
        while True:
            now = int(time.time())
            unixtimes = [int(key) for key in ircbot.rdb]
            oldtimes = [t for t in unixtimes if t <= now]
            if oldtimes:
                for oldtime in oldtimes:
                    for (channel, nick, message) in ircbot.rdb[oldtime]:
                        if message:
                            ircbot.msg(channel, nick + ': ' + message)
                        else:
                            ircbot.msg(channel, nick + '!')
                    del ircbot.rdb[oldtime]
                dump_database(ircbot.rfn, ircbot.rdb)
            time.sleep(2.5)

    targs = (ircbot,)
    t = threading.Thread(target=monitor, args=targs)
    t.start()

scaling = {
    'years': 365.25 * 24 * 3600,
    'year': 365.25 * 24 * 3600,
    'yrs': 365.25 * 24 * 3600,
    'y': 365.25 * 24 * 3600,

    'months': 29.53059 * 24 * 3600,
    'month': 29.53059 * 24 * 3600,
    'mo': 29.53059 * 24 * 3600,

    'weeks': 7 * 24 * 3600,
    'week': 7 * 24 * 3600,
    'wks': 7 * 24 * 3600,
    'wk': 7 * 24 * 3600,
    'w': 7 * 24 * 3600,

    'days': 24 * 3600,
    'day': 24 * 3600,
    'd': 24 * 3600,

    'hours': 3600,
    'hour': 3600,
    'hrs': 3600,
    'hr': 3600,
    'h': 3600,

    'minutes': 60,
    'minute': 60,
    'mins': 60,
    'min': 60,
    'm': 60,

    'seconds': 1,
    'second': 1,
    'secs': 1,
    'sec': 1,
    's': 1
}

periods = '|'.join(scaling.keys())
p_command = r'\.in ([0-9]+(?:\.[0-9]+)?)\s?((?:%s)\b)?:?\s?(.*)' % periods
r_command = re.compile(p_command)

def remind(ircbot, input):
    m = r_command.match(input.bytes)
    if not m:
        return ircbot.reply("Sorry, didn't understand the input.")
    length, scale, message = m.groups()

    length = float(length)
    factor = scaling.get(scale, 60)
    duration = length * factor

    if duration % 1:
        duration = int(duration) + 1
    else:
        duration = int(duration)

    t = int(time.time()) + duration
    reminder = (input.sender, input.nick, message)

    try:
        ircbot.rdb[t].append(reminder)
    except KeyError:
        ircbot.rdb[t] = [reminder]

    dump_database(ircbot.rfn, ircbot.rdb)

    if duration >= 60:
        w = ''
        if duration >= 3600 * 12:
            w += time.strftime(' on %d %b %Y', time.gmtime(t))
        w += time.strftime(' at %H:%MZ', time.gmtime(t))
        ircbot.reply('Okay, will remind%s' % w)
    else:
        ircbot.reply('Okay, will remind in %s secs' % duration)
remind.commands = ['in']
