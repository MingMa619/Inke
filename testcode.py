import wormwrapper_interface as wi
from time import sleep
import random
def run(info, resultlist):
    while True:
        wi.emitresult("dowork " + str(info["num"]), resultlist)
        sleep(random.randint(1, 10))