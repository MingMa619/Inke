import wormwrapper_admin as wa


if __name__ == '__main__':
    roomid = ["1498744828921016", "1498698295219962", "1499673850253349", "1498658015792556", "1498699161677158"]
    file1 = open('getcomments.py', 'rb')
    code = file1.read().decode('utf-8')
    file1.close()
    for i in range(0, len(roomid)):
        wa.wormwrapper_add_task(str(i), {"roomid": roomid[i]}, code)
    print("Add Tasks End.")