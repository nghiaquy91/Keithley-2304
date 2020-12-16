def createList(num):
    listData = []
    while num > 0:
        listData.append(0)
        num = num - 1
    return listData


def convertListToFloat(listData, num):
    dataFloat = []
    i = 0
    while i < num:
        dataFloat.append(float(listData[i]))
        i += 1
    return dataFloat