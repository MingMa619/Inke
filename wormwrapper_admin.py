import threading
import os
import sys
import time
import random
import pymongo
import sentence as st
import ctypes
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
lastruntime = 0
lastforcestoptime = 0


def wormwrapper_emit_instruction(instruct):
    instructiondata = instructionholder.find_one({"name": "instruction"})
    insstatus = instructionholder.find_one({"name": "status"})
    if instructiondata is None:
        instructionholder.insert_one({"name": "instruction", "list": [{"timestamp": 0.0, "data": "None"}]})
        instructiondata = instructionholder.find_one({"name": "instruction"})
    if insstatus is None:
        instructionholder.insert_one({"name": "status", "status": "free", "timestamp": 0})
        insstatus = instructionholder.find_one({"name": "status"})
    if insstatus["status"] != "free" and instruct == "run":
        print(st.wormwrapper_str4)
        return
    if insstatus["status"] != "running" and instruct == "forcestop":
        print(st.wormwrapper_str5)
        return
    if insstatus["status"] != "free" and instruct == "forcestop" and time.time()-insstatus["timestamp"] < 100:
        print(st.wormwrapper_str3)
        return
    if insstatus["status"] != "running" and instruct == "run" and time.time()-insstatus["timestamp"] < 100:
        print(st.wormwrapper_str3)
        return
    newlist = []
    for element in instructiondata["list"]:
        if time.time() - element["timestamp"] < 100:
            newlist.append(element)
    newlist.append({"timestamp": time.time(), "data": instruct})
    instructionholder.update_one({"name": "instruction"}, {"$set": {"list": newlist}})
    if instruct == "run":
        instructionholder.update_one({"name": "status"}, {"$set":{"status": "running", "timestamp": time.time()}})
        print(st.wormwrapper_str1)
    if instruct == "forcestop":
        instructionholder.update_one({"name": "status"}, {"$set":{"status": "free", "timestamp": time.time()}})
        print(st.wormwrapper_str2)


def wormwrapper_print_instruction():
    instructiondata = instructionholder.find_one({"name": "instruction"})
    insstatus = instructionholder.find_one({"name": "status"})
    if instructiondata is None:
        instructionholder.insert_one({"name": "instruction", "list": [{"timestamp": 0.0, "data": "None"}]})
        instructiondata = instructionholder.find_one({"name": "instruction"})
    if insstatus is None:
        instructionholder.insert_one({"name": "status", "status": "free", "timestamp": 0})
        insstatus = instructionholder.find_one({"name": "status"})
    for element in instructiondata["list"]:
        print(element)
    print(insstatus)


def wormwrapper_add_task(name, taskinfo, code):
    if placeholder.find_one({"name": str(name)}) is None:
        statusholder.insert_one({"name": str(name), "status": "free"})
        tasklist.insert_one({"name": str(name), "info": taskinfo, "code": code, "status": "free"})


def wormwrapper_delete_task(name):
    placeholder.delete_many({"name": str(name)})
    statusholder.find_one_and_delete({"name": str(name)})
    tasklist.find_one_and_delete({"name": str(name)})


def wormwrapper_virtualproc():
    file1 = open("testcode.py", "r")
    code = file1.read()
    file1.close()
    for i in range(0, 5):
        wormwrapper_add_task(i, {"num": i}, code)
    print(st.wormwrapper_str6)


def wormwrapper_clear_all():
    tasklist.delete_many({})
    placeholder.delete_many({})
    statusholder.delete_many({})
    instructionholder.delete_many({})
    print(st.wormwrapper_str7)


def wormwrapper_print_taskinfo(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print(st.wormwrapper_str8,taskname)
        return
    print(st.wormwrapper_str9, status["status"])
    resultlist = placeholder.find({"name": taskname}).sort("timestamp", pymongo.ASCENDING)
    print(st.wormwrapper_str10)
    for lists in resultlist:
        for element in lists["result"]:
            if element["timestamp"] != 0.0:
                print(element["timestamp"], ":", element["data"])
    print(st.wormwrapper_str11)


def wormwrapper_delete_one_task(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print(st.wormwrapper_str8, taskname)
        return
    if status["status"] == "running":
        wormwrapper_emit_instruction("deletetask " + taskname)
        print(st.wormwrapper_str12)
    else:
        wormwrapper_delete_task(name)


def wormwrapper_resume_one_task(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print(st.wormwrapper_str8, taskname)
        return
    if status["status"] == "error":
        print(st.wormwrapper_str13)
        statusholder.find_one_and_update({"name": taskname}, {"$set": {"status": "free"}})
        tasklist.find_one_and_update({"name": taskname}, {"$set": {"status": "free"}})
        print(st.wormwrapper_str14)
        return
    if status["status"] != "stop":
        print(st.wormwrapper_str15)
        return
    statusholder.find_one_and_update({"name": taskname}, {"$set": {"status": "free"}})
    tasklist.find_one_and_update({"name": taskname}, {"$set": {"status": "free"}})
    print(st.wormwrapper_str14)


def wormwrapper_stop_one_task(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print(st.wormwrapper_str8, taskname)
        return
    if status["status"] != "running":
        print(st.wormwrapper_str16)
        return
    wormwrapper_emit_instruction("stoptask " + taskname)
    statusholder.find_one_and_update({"name": taskname}, {"$set": {"status": "stop"}})
    tasklist.find_one_and_update({"name": taskname}, {"$set": {"status": "stop"}})
    print(st.wormwrapper_str17)


def wormwrapper_clear_one_task(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print(st.wormwrapper_str8, taskname)
        return
    placeholder.delete_many({"name": str(name)})
    print(st.wormwrapper_str18)


def wormwrapper_find_error():
    errortask = statusholder.find({"status": "error"})
    if errortask is None or errortask.count() == 0:
        print(st.wormwrapper_str19)
        return
    print(st.wormwrapper_str20)
    for task in errortask:
        print(task["name"])


if __name__ == '__main__':
    while True:
        print()
        print(st.wormwrapper_str21)
        line = sys.stdin.readline()
        if not line:
            break
        rawline = line
        line = str.lower(line)[:-1]
        if line == "emitvirtualproc":
            wormwrapper_virtualproc()
            continue
        if line == "clearall":
            wormwrapper_clear_all()
            continue
        if line == "run":
            wormwrapper_emit_instruction("run")
            print()
            continue
        if line == "finderror":
            wormwrapper_find_error()
        if line == "forcestop":
            wormwrapper_emit_instruction("forcestop")
            print()
            continue
        if line == "help":
            print(st.wormwrapper_str23)
            print(st.wormwrapper_str24)
            print(st.wormwrapper_str25)
            print(st.wormwrapper_str26)
            print(st.wormwrapper_str27)
            print(st.wormwrapper_str28)
            print(st.wormwrapper_str29)
            print(st.wormwrapper_str30)
            print(st.wormwrapper_str31)
            print(st.wormwrapper_str32)
            print(st.wormwrapper_str33)
            print(st.wormwrapper_str34)
            continue
        if line == "exit":
            break
        if line == "time":
            print(time.time())
            continue
        if line == "printinstruction":
            wormwrapper_print_instruction()
            continue
        if line.split(' ')[0] == "showinfo" and len(line.split(' ')) == 2:
            name = rawline.split(' ')[1][:-1]
            wormwrapper_print_taskinfo(name)
            continue
        if line.split(' ')[0] == "deletetask" and len(line.split(' ')) == 2:
            name = rawline.split(' ')[1][:-1]
            wormwrapper_delete_one_task(name)
            continue
        if line.split(' ')[0] == "resumetask" and len(line.split(' ')) == 2:
            name = rawline.split(' ')[1][:-1]
            wormwrapper_resume_one_task(name)
            continue
        if line.split(' ')[0] == "stoptask" and len(line.split(' ')) == 2:
            name = rawline.split(' ')[1][:-1]
            wormwrapper_stop_one_task(name)
            continue
        if line.split(' ')[0] == "cleartask" and len(line.split(' ')) == 2:
            name = rawline.split(' ')[1][:-1]
            wormwrapper_clear_one_task(name)
            continue
    print(st.wormwrapper_str22)

