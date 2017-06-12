"""
    Interpreter
    -----------

    Runs a block of FoxDot code. Designed to be overloaded
    for other language communication

"""
from subprocess import Popen
from subprocess import PIPE, STDOUT
from datetime import datetime
from config import *
import sys
import re
import time
import threading

DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

def compile_regex(kw):
    """ Takes a list of strings and returns a regex that
        matches each one """
    return re.compile(r"(?<![a-zA-Z.])(" + "|".join(kw) + ")(?![a-zA-Z])")

SEPARATOR = ":"; _ = " %s " % SEPARATOR

class Clock:
    def __init__(self):
        self.time = time.clock()
    def kill(self):
        return
    def reset(self):
        self.time = 0
        self.mark = time.time()
    def get_time(self):
        return 0
    def set_time(self, t, timestamp):
        self.time = t
    def get_bpm(self):
        return 60.0
    def now(self):
        return time.clock()

def colour_format(text, colour):
    return '<colour="{}">{}</colour>'.format(colour, text)
    

class Interpreter(Clock):
    lang     = None
    clock    = None
    re       = compile_regex([])
    stdout   = None
    def evaluate(self, string, name, colour="White"):
        """ Handles the printing of the execute code to screen with coloured
            names and formatting """
        # Split on newlines
        string = [line.strip() for line in string.split("\n") if len(line.strip()) > 0]

        if len(string) > 0:        
            print(colour_format(name, colour) + _ + string[0])
            # Use ... for the remainder  of the  lines
            n = len(name)
            for i in range(1,len(string)):
                print(colour_format("." * n, colour) + _ + string[i])
        return
    def stop_sound(self):
        return ""

class FoxDotInterpreter(Interpreter):
    def __init__(self):
        import FoxDot

        self.lang  = FoxDot
        self.clock = FoxDot.Clock
        self.counter = None # Is the number of "beats"
        self.last_bpm = self.get_bpm()
        self.last_start_time = 0

        try:

            self.keywords = list(FoxDot.get_keywords()) + list(FoxDot.SynthDefs) + ["play"]

        except AttributeError:

            self.keywords = ['>>']

        self.re = compile_regex(self.keywords)

    def kill(self):
        self.clock.stop()

    def stop_sound(self):
        return "Clock.clear()"

    def get_time(self):
        return self.clock.start_time

    def set_time(self, clock_time, time_stamp):
        self.clock.start_time = clock_time
        return
            
    def evaluate(self, *args, **kwargs):
        """ Sends code to FoxDot instance and prints any error text """
        Interpreter.evaluate(self, *args, **kwargs)

        response = self.lang.execute(args[0], verbose=False)

        if response.startswith("Traceback"):

            print(response)
        
        return


class SuperColliderInterpreter(Interpreter):
    def __init__(self):
        import OSC

        # Get password for Troop quark
        from getpass import getpass
        self.__password = getpass("Enter the password for your SuperCollider Troop Quark: ")

        # Connect to OSC client
        self.host = 'localhost'
        self.port = 57120
        self.lang = OSC.OSCClient()
        self.lang.connect((self.host, self.port))

        # Define a function to produce new OSC messages
        self.new_msg = lambda: OSC.OSCMessage()

    def stop_sound(self):
        return "s.freeAll"
        
    def evaluate(self, *args, **kwargs):
        Interpreter.evaluate(self, *args, **kwargs)
        msg = self.new_msg()
        msg.setAddress("/troop")
        msg.append([self.__password, string])
        self.lang.send(msg)
        return

class TidalInterpreter(Interpreter):
    def __init__(self):
        self.lang = Popen(['ghci'], shell=True, universal_newlines=True,
                          stdin=PIPE,
                          stdout=PIPE,
                          stderr=STDOUT)

        self.lang.stdin.write("import Sound.Tidal.Context\n")
        self.lang.stdin.write(":set -XOverloadedStrings\n")
        self.lang.stdin.write("(cps, getNow) <- bpsUtils\n")

        d_vals = range(1,10)
        
        for n in d_vals:
            self.lang.stdin.write("(d{}, t{}) <- superDirtSetters getNow\n".format(n, n))

        self.lang.stdin.write("let hush = mapM_ ($ silence) [d1,d2,d3,d4,d5,d6,d7,d8,d9]\n")

        self.keywords  = ["d{}".format(n) for n in d_vals]
        self.keywords += ["\$", "#", "hush"] # add string regex?
        self.re = compile_regex(self.keywords)

        while self.stdout() > 0:

            pass

    def evaluate(self, *args, **kwargs):
        Interpreter.evaluate(self, *args, **kwargs)
        string = args[0]
        self.lang.stdin.write(":{\n"+string+"\n:}\n")
        threading.Thread(target=self.stdout).start()
        return

    def stdout(self):
        time.sleep(0.1)
        self.lang.stdout.seek(0,2)      # Doesn't give us the real end -- threading the issue?
        buf_end = self.lang.stdout.tell()
        self.lang.stdout.seek(0)
        text = self.lang.stdout.read(buf_end)
        print(text)
        return len(text)

    def stop_sound(self):
        return "hush"

    def kill(self):
        self.lang.communicate()
        self.lang.kill()        

langtypes = { FOXDOT        : FoxDotInterpreter,
              TIDAL         : TidalInterpreter,
              SUPERCOLLIDER : SuperColliderInterpreter }
