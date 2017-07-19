import threading
import sys
import traceback
import os
import time
import random
import pymongo
import ctypes
import importlib.util
import string
from time import ctime, sleep
from bson.objectid import ObjectId
dburi = "mongodb://127.0.0.1"
client = pymongo.MongoClient(dburi)
taskdb = client["tasks"]
tasklist = taskdb["tasks"]

placeholder = taskdb["result"]
placeholder.ensure_index('name', unique=False)
statusholder = taskdb["status"]
statusholder.ensure_index('name', unique=True)
instructionholder = taskdb["instruction"]
nowinstruction = ""
instructiontimestamp = time.time()
nowtaskname = ""
exc_traceback = ""
thread_error = False

def dowork(info, resultlist, modulename):
    global exc_traceback, thread_error
    module = importlib.import_module(modulename)
    try:
        module.run(info, resultlist)
        while True:
            print(module.wormwrapper_str1)
            emitresult("dowork "+str(info["num"]), resultlist)
            sleep(random.randint(1,10))
    except Exception as e:
        thread_error = True
        exc_traceback = ''.join(traceback.format_exception(*sys.exc_info()))


def update(name, resultlist):
    while True:
        placeholder.insert_one({"name": name, "timestamp": time.time(), "result": resultlist})
        resultlist.clear()
        sleep(10+random.randint(1,5))


def emitresult(text, resultlist):
    resultlist.append({"timestamp":time.time(), "data":str(text)})
    print(time.time(), text)


def wormwrapper_terminate_thread(thread):
    if not thread.isAlive():
        return
    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def wormwrapper_get_instruction():
    global nowinstruction, instructiontimestamp
    nowinstruction = ""
    instructiondata = instructionholder.find_one({"name": "instruction"})
    if instructiondata is None:
        instructionholder.insert_one({"name": "instruction", "list": [{"timestamp":0.0, "data":"None"}]})
        instructiondata = instructionholder.find_one({"name": "instruction"})
    for instruction in instructiondata["list"]:
        if instruction["data"] != "None":
            if instruction["timestamp"] > instructiontimestamp:
                nowinstruction = instruction["data"]
                print("modify: ",nowinstruction)
                instructiontimestamp = instruction["timestamp"]
                break
    if nowinstruction == "" or nowinstruction is None:
        return "None"
    return nowinstruction


threads = []
resultlist = []


def wormwrapper_delete_task(name):
    placeholder.delete_many({"name": str(name)})
    statusholder.find_one_and_delete({"name": str(name)})
    tasklist.find_one_and_delete({"name": str(name)})


def wormwrapper_dostuck():
    while True:
        print("Wait for running...")
        insstatus = instructionholder.find_one({"name": "status"})
        if insstatus is None:
            instructionholder.insert_one({"name": "status", "status": "free", "timestamp": 0})
            insstatus = instructionholder.find_one({"name": "status"})
        if insstatus["status"] == "running":
            oneinfo = tasklist.find_one_and_delete({"status": "free"})
            if oneinfo is not None:
                oneinfo["status"] = "running"
                tasklist.insert_one(oneinfo)
                return oneinfo["name"], oneinfo["info"], oneinfo
        sleep(8 + random.randint(1, 10))


def wormwrapper_dogetinstruction(nowtaskname, oneinfo):
    global resultlist, thread_error, exc_traceback
    while True:
        if thread_error:
            global resultlist
            print("thread has some error")
            for t in threads:
                wormwrapper_terminate_thread(t)
            resultlist.append({"timestamp":time.time(), "data":exc_traceback})
            placeholder.insert_one({"name": nowtaskname, "timestamp": time.time(), "result": resultlist})
            resultlist.clear()
            oneinfo["status"] = "error"
            statusholder.update_one({"name": nowtaskname}, {"$set": {"status": "error"}})
            tasklist.update_one({"name": oneinfo["name"]}, {"$set": {"status": "error"}})
            thread_error = False
            exc_traceback = ""
            break
        instruction = wormwrapper_get_instruction()
        print("Try to get an instruction")
        print(instruction)
        if instruction == "forcestop":
            print('stoptask')
            for t in threads:
                wormwrapper_terminate_thread(t)
            placeholder.insert_one({"name": nowtaskname, "timestamp": time.time(), "result": resultlist})
            resultlist.clear()
            oneinfo["status"] = "stop"
            statusholder.update_one({"name": nowtaskname}, {"$set": {"status": "stop"}})
            tasklist.update_one({"name": oneinfo["name"]}, {"$set": {"status": "stop"}})
            break
        if instruction.split(' ')[0] == "deletetask":
            deletetaskname = instruction.split(' ')[1]
            if deletetaskname == nowtaskname:
                for t in threads:
                    wormwrapper_terminate_thread(t)
                wormwrapper_delete_task(deletetaskname)
                break
        if instruction.split(' ')[0] == "stoptask":
            stoptaskname = instruction.split(' ')[1]
            if stoptaskname == nowtaskname:
                print('stoptask')
                for t in threads:
                    wormwrapper_terminate_thread(t)
                placeholder.insert_one({"name": nowtaskname, "timestamp": time.time(), "result": resultlist})
                resultlist.clear()
                oneinfo["status"] = "stop"
                statusholder.update_one({"name": nowtaskname}, {"$set": {"status" : "stop"}})
                tasklist.update_one({"name": oneinfo["name"]}, {"$set": {"status" : "stop"}})
                break
        sleep(20 + random.randint(1, 10))


if __name__ == '__main__':
    while True:
        name, info, oneinfo = wormwrapper_dostuck()
        nowtaskname = name
        threads.clear()
        resultlist.clear()
        statusholder.update_one({"name": nowtaskname}, {"$set": {"status": "running"}})
        modulefilename = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        while os.path.exists(modulefilename+".py"):
            modulefilename = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        file1 = open(modulefilename+".py", 'w')
        file1.write(oneinfo["code"])
        file1.close()
        resultlist = []
        t1 = threading.Thread(target=dowork, args=(info, resultlist, modulefilename))
        t2 = threading.Thread(target=update, args=(name, resultlist,))
        threads.append(t1)
        threads.append(t2)
        for t in threads:
            t.setDaemon(True)
            t.start()
        wormwrapper_dogetinstruction(nowtaskname, oneinfo)
