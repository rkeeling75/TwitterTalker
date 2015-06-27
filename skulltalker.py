from oauth.oauth import OAuthRequest, OAuthSignatureMethod_HMAC_SHA1
from hashlib import md5

import json, urllib, os, random, urllib, urllib2, subprocess, time,
pycurl, subprocess, sys, re

#you might have to do a sudo apt-get install X for some of these packages
#things like pytho-oauth, mplayer, pycurl, espeak

# twitter oauth keys
#USE YOUR OWN KEYS
CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
MAX_LEN = 100
TWITTER_HANDLE = '@XXXXXXXXXX'

#converts a given phrase to a url that Google's Text to Speech API
#uses. WARNING, Google only lets you use 100 characters max. No error
#checking here, that is up to you to impliment
def getGoogleSpeechURL(phrase):
    googleURL = "http://translate.google.com/translate_tts?tl=en&"
    parameters = {'q': phrase}
    data = urllib.urlencode(parameters)
    googleURL = "%s%s" % (googleURL, data)
    return googleURL

#given a file name, return a random line from that file
#no error checking
def random_line(afileName):
    with open(afileName, "r") as afile:
        line = next(afile)
        for num, aline in enumerate(afile):
            if random.randrange(num + 2): continue
            line = aline
        return line

#tries to use the Google API, if we aren't online then fall back to the internal
#TTS, espeak
def speakSpeechFromText(phrase):
    if internet_on():
        googleSpeechURL = getGoogleSpeechURL(phrase)
        subprocess.call(['mplayer', '-ao', 'alsa', '-really-quiet',
'-noconsolecontrols', googleSpeechURL])
    else:
        print phrase
        subprocess.call(['espeak', '-ven+f2', '-k5', '-s120', phrase])

#if you want to save the TTS results from Google to a file
def saveSpeechMP3(phrase, filename):
        googleSpeechURL = getGoogleSpeechURL(phrase)
        downloadFile(googleSpeechURL, filename)

#generic routine to save a url to a file
def downloadFile(url, fileName):
    fp = open(fileName, "wb")
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.WRITEDATA, fp)
    curl.perform()
    curl.close()
    fp.close()

#Well, is it?
def internet_on():
    try:
        #the url is a google IP. numeric url avoids a DNS hit
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

#get a random file from a given directory
def randomFile(path):
    return path + random.choice(os.listdir(path))




# class for managing tokens, Twitter stuff
class Token(object):
    def __init__(self,key,secret):
        self.key = key
        self.secret = secret

    def _generate_nonce(self):
        random_number = ''.join(str(random.randint(0, 9)) for i in range(40))
        m = md5(str(time.time()) + str(random_number))
        return m.hexdigest()

# talking twitter client
class TalkingTwitterStreamClient:
    def __init__(self, streamURL):
        self.streamURL = streamURL
        self.buffer = ""
        self.conn = pycurl.Curl()
        self.conn.setopt(pycurl.URL, self.streamURL)
        self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
        self.conn.perform()

    def on_receive(self, data):
        sys.stdout.write(".")
        self.buffer += data
        if data.endswith("\n") and self.buffer.strip():
            content = json.loads(self.buffer)
            self.buffer = ""
            #debug - output json from buffer
            print content
            if "friends" in content:
                self.friends = content["friends"]

            if "text" in content:
                print u"{0[user][name]}:
{0[text]}".format(content).encode('utf-8')
                speakSpeechFromText(u"A tweet from
{0[user][name]}".format(content))
                #if you'd rather download the sound file instead of
(or in addition to) uncomment below
                #downloadSpeechFromText(u"A tweet from
{0[user][name]}".format(content), "./tweet.mp3")
                textToSpeak = u"{0[text]}".format(content)
                #by default the text back from Twitter is exactly what is typed
                #which includes the @TheMakerSkull, so let's remove
that from the
                #front of the twit if it exists, this could cause issues but
                #but its the best solution I have right now
                if textToSpeak.startswith(TWITTER_HANDLE):
                    textToSpeak = textToSpeak.replace(TWITTER_HANDLE, '')
                textToSpeak = textToSpeak.strip()
                #debugging, in the skull you won't see these messages
                print textToSpeak

                #Start the spliting of the message if it is longer than
                #what we can handle, in this case the limiter is Google's API
                #Espeak doesn't have this problem, you can always change this
                #in the constants above
                #We could check if we are online before we split but that would
                #just be a 'nice to have' and not worth it right now since the
                #assumption is that we will always be online
                fullMsg = textToSpeak
                # Split our full text by any available punctuation
                parts = re.split("[\.\,\;\:]", fullMsg)


                # The final list of parts to send to Google TTS or the internal
                processedParts = []

                #Time to split this stack
                while len(parts)>0: # While we have parts to process
                    part = parts.pop(0) # Get first entry from our list

                    if len(part)>MAX_LEN:
                        # We need to do some cutting
                        cutAt = part.rfind(" ",0,MAX_LEN) # Find the
last space within the bounds of our MAX_LEN
                        cut = part[:cutAt]

                        # We need to process the remainder of this part next
                        # Reverse our queue, add our remainder to the
end, then reverse again
                        parts.reverse()
                        parts.append(part[cutAt:])
                        parts.reverse()
                    else:
                        # No cutting needed
                        cut = part

                    cut = cut.strip() # Strip any whitespace
                    if cut is not "": # Make sure there's something left to read
                        # Add into our final list
                        processedParts.append(cut.strip())

                for part in processedParts:
                    speakSpeechFromText(part)

# get the url needed to open the twitter user stream, including
signature after authentication
def getTwitterUserStreamURL():
    STREAM_URL = "https://userstream.twitter.com/2/user.json"

    access_token = Token(ACCESS_TOKEN,ACCESS_TOKEN_SECRET)
    consumer = Token(CONSUMER_KEY,CONSUMER_SECRET)

    parameters = {
        'oauth_consumer_key': CONSUMER_KEY,
        'oauth_token': access_token.key,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_nonce': access_token._generate_nonce(),
        'oauth_version': '1.0',
    }

    oauth_request = OAuthRequest.from_token_and_callback(access_token,
                    http_url=STREAM_URL,
                    parameters=parameters)
    signature_method = OAuthSignatureMethod_HMAC_SHA1()
    signature = signature_method.build_signature(oauth_request,
consumer, access_token)

    parameters['oauth_signature'] = signature
    data = urllib.urlencode(parameters)
    return "%s?%s" % (STREAM_URL,data)


#was used for reading from a file and debugging
#filePath = "/home/randy/TalkingSkullPhrases.txt"
#outputPath = "/home/pi/soundfiles/"
#minWaitSeconds = 5
#maxWaitSeconds = 15

#this starts it all
print ("Started but waiting 30 seconds to give the pi time to get online")
time.sleep(30)
speakSpeechFromText("It is nice to see all my favorite makers again.")
speakSpeechFromText("My name is XXXXX.")
if internet_on():
    speakSpeechFromText("You can tweet me at XXXXX.")
    speakSpeechFromText("I am listening!")
else:
    speakSpeechFromText("I cannot find an internet connection; fix me please?")
    speakSpeechFromText("I will put myself to sleep while you fix the problem.")
    speakSpeechFromText("Good Night")
    sys.exit("No internet Connection Found")




client = TalkingTwitterStreamClient(getTwitterUserStreamURL())


#more file reading and debugging logic
'''
while True:
    file = randomFile(outputPath)
    subprocess.call(['mplayer',  file])
    wait = random.randint(minWaitSeconds, maxWaitSeconds)
    print "Waiting for " + str(wait) + " seconds"
    time.sleep(wait)

'''
'''
counter = 1

with open(filePath, "r") as afile:
    for line in afile:
        print line
        counterstring = "%01d" % counter
        saveSpeechMP3(line, outputPath + counterstring + ".mp3")
        counter += 1

speakSpeechFromText (random_line(filePath))
'''
