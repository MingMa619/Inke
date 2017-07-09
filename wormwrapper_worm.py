import threading
import os
import time
import random
import pymongo
import ctypes
from time import ctime, sleep
from bson.objectid import ObjectId
dburi = "mongodb://127.0.0.1"
client = pymongo.MongoClient(dburi)
taskdb = client["tasks"]
freetask = taskdb["free"]
busytask = taskdb["busy"]
placeholder = taskdb["result"]
placeholder.ensure_index('name', unique=True)
statusholder = taskdb["status"]
statusholder.ensure_index('name', unique=True)
instructionholder = taskdb["instruction"]
nowinstruction = ""
instructiontimestamp = 0.0
nowtaskname = ""


def dowork(info, resultlist):
    while True:
        emitresult("dowork "+str(info["num"]), resultlist)
        sleep(random.randint(1,10))


def update(name, resultlist):
    while True:
        placeholder.update_one({"name": name}, {"$set": {"result": resultlist}})
        sleep(10+random.randint(1,5))


def emitresult(text, resultlist):
    resultlist.append({"timestamp":time.time(), "data":text})
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
        statusholder.insert_one({"name": "instruction", "list": [{"timestamp":0.0, "data":"None"}]})
        instructiondata = instructionholder.find_one({"name": "instruction"})
    for instruction in instructiondata["list"]:
        if instruction["data"] != "None":
            if instruction["timestamp"] > instructiontimestamp:
                nowinstruction = instruction["data"]
                instructiontimestamp = instruction["timestamp"]
                break
    if nowinstruction == "" or nowinstruction is None:
        return "None"
    return nowinstruction


threads = []
resultlist = []


def wormwrapper_delete_task(name):
    placeholder.find_one_and_delete({"name": str(name)})
    statusholder.find_one_and_delete({"name": str(name)})
    freetask.find_one_and_delete({"name": str(name)})
    busytask.find_one_and_delete({"name": str(name)})


def wormwrapper_dostuck():
    while True:
        print("Wait for running...")
        insstatus = instructionholder.find_one({"name": "status"})
        if insstatus is None:
            instructionholder.insert_one({"name": "status", "status": "free", "timestamp": 0})
            insstatus = instructionholder.find_one({"name": "status"})
        if insstatus["status"] == "running":
            oneinfo = freetask.find_one_and_delete({})
            if oneinfo is not None:
                busytask.insert_one(oneinfo)
                return oneinfo["name"], oneinfo["info"]
        sleep(8 + random.randint(1, 10))


def wormwrapper_dogetinstruction():
    while True:
        instruction = wormwrapper_get_instruction()
        print(instruction)
        if instruction == "forcestop":
            for t in threads:
                wormwrapper_terminate_thread(t)
            update(nowtaskname, resultlist)
            break
        if instruction.split(' ')[0] == "deletetask":
            deletetaskname = instruction.split(' ')[1]
            if deletetaskname == nowtaskname:
                for t in threads:
                    wormwrapper_terminate_thread(t)
                wormwrapper_delete_task(deletetaskname)
                break
        sleep(20 + random.randint(1, 10))


if __name__ == '__main__':
    while True:
        name, info = wormwrapper_dostuck()
        nowtaskname = name
        threads.clear()
        resultlist.clear()
        place = placeholder.find_one({"name": nowtaskname})
        statusholder.update_one({"name": nowtaskname}, {"$set": {"status": "running"}})
        resultlist = place["result"]
        t1 = threading.Thread(target=dowork, args=(info, resultlist,))
        t2 = threading.Thread(target=update, args=(name, resultlist,))
        threads.append(t1)
        threads.append(t2)
        for t in threads:
            t.setDaemon(True)
            t.start()
        wormwrapper_dogetinstruction()
