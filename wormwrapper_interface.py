import time
def emitresult(text, resultlist):
    resultlist.append({"timestamp":time.time(), "data":str(text)})
    print(time.time(), text)