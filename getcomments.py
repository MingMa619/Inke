# coding: utf-8
import urllib
import urllib.request as urllib2
import re
import sys
import difflib
import json
from datetime import datetime
import random
import time
import socket
from websocket import create_connection, WebSocket
import wormwrapper_interface as wi
from time import sleep
import random
import websocket



def get_socketio(roomid, resultlist): #送出多少，收到多少
    
    index_url = r"http://webapi.busi.inke.cn/web/live_share_pc?uid=59127812&id=" + roomid
    #http://47.93.153.239:81/socket.io/1/?uid=&place=room&sid=1&roomid=1498650479482163&token=&time=1498654844&nonce=m9by1x3OL8&sec=55178a79b66d4f135165232409c12c6b&t=1498654844010
    #http://47.93.153.239:81/socket.io/1/websocket/wUSTUOeTLRYAZrlDzFzU?uid=&place=room&sid=1&roomid=1498650479482163&token=&time=1498654844&nonce=m9by1x3OL8&sec=55178a79b66d4f135165232409c12c6b
    request = urllib2.Request(index_url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586')
    
    while True:
        try:
            page = urllib2.urlopen(request, data=None, timeout=5)
            text = page.read()
            break
        except Exception as e:
            continue
    wi.emitresult(text, resultlist)
    text = text.decode('utf-8')
    #"sio_ip":"47.93.153.239:81"
    ip = re.findall("\"sio_ip\":\".*:81\"", text)[0]
    wi.emitresult(ip, resultlist)
    wi.emitresult(time.time(), resultlist)
    nonce = re.findall("\"nonce\":\"\w+\"", text)[0]
    wi.emitresult(nonce, resultlist)
    # "sec":"758899abc931e8627d4342195a436526"
    sec = re.findall("\"sec\":\"\w+\"", text)[0]
    wi.emitresult(sec, resultlist)
    timex = re.findall(r'\"time\":\d+', text)[0]
    wi.emitresult(timex, resultlist)
    return ip, nonce, sec, timex

def get_real_chaturl(roomid, ip, nonce, sec, timex, resultlist):
    ip = ip.split("\"")[-2]
    nonce = nonce.split("\"")[-2]
    sec = sec.split("\"")[-2]
    timex = timex.split(":")[-1]
    wi.emitresult(ip+' '+nonce+' '+sec, resultlist)
    getPathURL = "http://" + ip + "/socket.io/1/?uid=&place=room&sid=1&roomid=" + roomid + "&token=&time=" + timex + "&nonce=" + nonce + "&sec=" + sec
    wi.emitresult(getPathURL, resultlist)
    
    #ws = create_connection(url)
    #result =  ws.recv()
    #print "Received '%s'" % result
    #ws.close()
    headersx = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586", "Connection": "Keep-Alive", "Accept-Encoding": "gzip, deflate", "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4"}
    #request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586')
    #request.add_header(headers)
    request = urllib2.Request(getPathURL, headers = headersx)
    
    while True:
        try:
            page = urllib2.urlopen(request, data=None, timeout=5)
            text = page.read()
            break
        except Exception as e:
            continue
    wi.emitresult(text, resultlist)
    text = text.decode('utf-8')
    path = text.split(":")[0]
    #http://47.93.153.239:81/socket.io/1/websocket/wUSTUOeTLRYAZrlDzFzU?uid=&place=room&sid=1&roomid=1498650479482163&token=&time=1498654844&nonce=m9by1x3OL8&sec=55178a79b66d4f135165232409c12c6b
    chaturl = "ws://" + ip + "/socket.io/1/websocket/" + path + "?uid=&place=room&sid=1&roomid=" + roomid + "&token=&time=" + str(int(time.time())) + "&nonce=" + nonce + "&sec=" + sec
    wi.emitresult(chaturl, resultlist)
    return chaturl

def get_chatContent(chaturl, resultlist):
    ws = create_connection(chaturl)
    while True:
        try:
            result =  ws.recv()
            wi.emitresult("Received '%s'" % result, resultlist)
        except Exception as e:
            break
    ws.close()


def run(info, resultlist):
    roomid = info['roomid']
    websocket.enableTrace(True)
    ip, nounce, sec, timex = get_socketio(roomid, resultlist)
    chaturl = get_real_chaturl(roomid, ip, nounce, sec, timex, resultlist)
    while True:
        get_chatContent(chaturl, resultlist)