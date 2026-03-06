import json
import re

with open('input.json', 'r', encoding='utf-8') as json_file:
    not_marked_data = json.load(json_file)
with open('REGEX.json', 'r', encoding='utf-8') as json_file:
    regex= json.load(json_file)
mark_types = ["СилаРекомендации", "Цель", "Состояние", "Популяция", "Действие", "Модификатор"]

N = 200
M = 100
def iou(span1, span2):
    start1, end1 = span1
    start2, end2 = span2
    intersection = max(0, min(end1, end2) - max(start1, start2))
    union = (end1 - start1) + (end2 - start2) - intersection
    if union == 0:
        return 0.0
    return intersection / union


regex_marks = []
for item in not_marked_data:
    current_regex_mark = []
    if M <= item["data"]["id"] <= N:
        id = item["data"]["id"]
        txt = item["data"]["text"]
        for type in mark_types:

            if (id == 180):  # 180-ый элемент имеет настолько длинный текст, что регулярка выполняется сликшом долго
                marks = []
            else:
                marks = re.findall(regex[type], item["data"]["text"])

            for mark in marks:
                start = txt.find(mark)
                if start == 0:
                    continue
                end = start + len(mark)
                current_regex_mark.append([start, end, type, mark])
        regex_marks.append([txt, id, current_regex_mark])

# for item in regex_marks:
#     print(item[1])
#     for a in item[2]:
#         print(a)
#     print()

with open('labelstudio_import.json', 'r', encoding='utf-8') as json_file:
    marked_data = json.load(json_file)
human_marks = []
for item in marked_data:
    current_human_mark = []
    if M <= item["data"]["id"] <= N:
        txt = item["data"]["text"]
        id = item["data"]["text"]
        for mark in item["annotations"][0]["result"]:
            start = mark["value"]["start"]
            end = mark["value"]["end"]
            mark_txt = mark["value"]["text"]
            type = mark["value"]["labels"][0]
            current_human_mark.append([start, end, type, mark_txt])
        human_marks.append([txt, id, current_human_mark])

avr_iou = {}
iou_count = {}
threshold = 0.5

# оставь надежду всяк сюда входящий
for type in mark_types:  #сравнениваем человека и регулярки
    current_iou = []
    for i in range(N - M):
        hm = []                         # hm - список с элементами вида: [start, end], таких, что
        for item in human_marks[i][2]:  # тип соответсвующей метки == type
            if type == item[2]:
                hm.append([item[0], item[1]])
        rm = []
        for item in regex_marks[i][2]:
            if type == item[2]:         # аналогично rm
                rm.append([item[0], item[1]])
        hm.sort(key=lambda x: x[0])
        rm.sort(key=lambda x: x[0])

        for j in range(abs(len(hm) - len(rm))): # за разницу между колличеством меток накидываем нулевых метрик
            current_iou.append(0.0)

        if (len(hm) == 0) or (len (rm) == 0):
            continue
            
        while (len(hm) > len(rm)):  # пока не исправим разницу удаляем лишние элементы
            if(hm[0][1] > rm[0][0]): # если конец 1 элемента бОльшего списка правее, чем начало 1 элемента меньшего то удаляем последний элемент бОльшего списка
                hm.pop()
            else:               # иначе первый
                hm.pop(0)
        while (len(rm) > len(hm)):
            if(rm[0][1] > hm[0][0]):
                rm.pop()
            else:
                rm.pop(0)
        # cравняли списки
        for j in range(len(hm)):
            current_iou.append(iou(hm[j], rm[j]))
    if len(current_iou) != 0:
        avr_iou[type] = sum(current_iou) / len(current_iou)
        iou_count[type] = sum([1 for l in current_iou if l >= threshold])
    else:
        avr_iou[type] = 0
        iou_count[type] = 0

print(f"From {M} to {N}")
print(f"IoU threshold: {threshold}\tMax IoU count: {N - M}")
print()
print(f"{"Mark":^17} {"Avr IoU":^20} {"IoU count":^9}")
for type in mark_types:
    print(f"{type+':':<17} {avr_iou[type]:<20} {iou_count[type]:^9}")
print()


