import threading
import os
import sys
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
        print("Worms are running...")
        return
    if insstatus["status"] != "running" and instruct == "forcestop":
        print("Worms are not running...")
        return
    if insstatus["status"] != "free" and instruct == "forcestop" and time.time()-insstatus["timestamp"] < 100:
        print("You must wait for 100 seconds between run and forcestop...")
        return
    if insstatus["status"] != "running" and instruct == "run" and time.time()-insstatus["timestamp"] < 100:
        print("You must wait for 100 seconds between run and forcestop...")
        return
    newlist = []
    for element in instructiondata["list"]:
        if time.time() - element["timestamp"] < 100:
            newlist.append(element)
    newlist.append({"timestamp": time.time(), "data": instruct})
    instructionholder.update_one({"name": "instruction"}, {"$set": {"list": newlist}})
    if instruct == "run":
        instructionholder.update_one({"name": "status"}, {"$set":{"status": "running", "timestamp": time.time()}})
        print("This instruction will cause all worms running soon.")
    if instruct == "forcestop":
        instructionholder.update_one({"name": "status"}, {"$set":{"status": "free", "timestamp": time.time()}})
        print("This instruction will cause all worms stop and upload result.")


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


def wormwrapper_add_task(name, taskinfo):
    if placeholder.find_one({"name": str(name)}) is None:
        placeholder.insert_one({"name": str(name), "result": [{"timestamp": 0.0, "data": "inidata"}]})
        statusholder.insert_one({"name": str(name), "status": "free"})
        freetask.insert_one({"name": str(name), "info": taskinfo})


def wormwrapper_delete_task(name):
    placeholder.find_one_and_delete({"name": str(name)})
    statusholder.find_one_and_delete({"name": str(name)})
    freetask.find_one_and_delete({"name": str(name)})
    busytask.find_one_and_delete({"name": str(name)})


def wormwrapper_virtualproc():
    for i in range(0, 100):
        wormwrapper_add_task(i, {"num": i})
    print("Finished generate virtual processes.")


def wormwrapper_clear_all():
    freetask.delete_many({})
    busytask.delete_many({})
    placeholder.delete_many({})
    statusholder.delete_many({})
    instructionholder.delete_many({})
    print("Finished clearing all tasks.")


def wormwrapper_print_taskinfo(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print("No task named ",taskname)
        return
    print("status of task: ", status["status"])
    place = placeholder.find_one({"name": taskname})
    print("result of task:")
    for element in place["result"]:
        if element["timestamp"] != 0.0:
            print(element["timestamp"], ":", element["data"])
    print("print taskinfo of task ", taskname, " end...")


def wormwrapper_delete_one_task(taskname):
    status = statusholder.find_one({"name": taskname})
    if status is None:
        print("No task named ", taskname)
        return
    wormwrapper_emit_instruction("deletetask " + taskname)
    print("This task will be deleted in a short time")


if __name__ == '__main__':
    while True:
        print()
        print("Please Input Command, type help to show help message:")
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
            print()
            print("execute instruction run...")
            print()
            wormwrapper_emit_instruction("run")
            print()
            continue
        if line == "forcestop":
            print()
            print("execute instruction forcestop...")
            print()
            wormwrapper_emit_instruction("forcestop")
            print()
            continue
        if line == "help":
            print("emitvirtualproc to emit some virtual proc")
            print("clearall to clear all tasks, be careful to use that")
            print("run to begin")
            print("forcestop to stop")
            print("exit to exit")
            print("showinfo i to show information of task i")
            print("deletetask i to delete a task i")
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
    print("Thank you for your using it.")

