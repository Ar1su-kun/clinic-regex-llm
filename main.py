import json
import re
import label_studio_sdk

N = 200
M = 100
THRESHOLD = 0.5
LABEL_STUDIO_URL = ''
LABEL_STUDIO_API_KEY = ''

with open('input.json', 'r', encoding='utf-8') as json_file:
        not_marked_data = json.load(json_file)
with open('REGEX.json', 'r', encoding='utf-8') as json_file:
        regex= json.load(json_file)
with open('labelstudio_import.json', 'r', encoding='utf-8') as json_file:
        marked_data = json.load(json_file)

MARK_TYPES = ["СилаРекомендации", "Цель", "Состояние", "Популяция", "Действие", "Модификатор"]


def iou(span1, span2):
    start1, end1 = span1
    start2, end2 = span2
    intersection = max(0, min(end1, end2) - max(start1, start2))
    union = (end1 - start1) + (end2 - start2) - intersection
    if union == 0:
        return 0.0
    return intersection / union


def input_regex():
    regex_marks = []
    for item in not_marked_data:
        current_regex_mark = []
        if M <= item["data"]["id"] <= N:
            id = item["data"]["id"]
            txt = item["data"]["text"]
            for type in MARK_TYPES:

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
    return regex_marks


def input_marked_data(str):
    input_marks = []
    for item in marked_data:
        current_human_mark = []
        if M <= item["data"]["id"] <= N:
            txt = item["data"]["text"]
            id = item["data"]["text"]
            for mark in item[str][0]["result"]:
                start = mark["value"]["start"]
                end = mark["value"]["end"]
                mark_txt = mark["value"]["text"]
                type = mark["value"]["labels"][0]
                current_human_mark.append([start, end, type, mark_txt])
            input_marks.append([txt, id, current_human_mark])
    return input_marks

def compare_marks(mark1, mark2): # оставь надежду всяк сюда входящий
    avr_iou = {}
    iou_count = {}
         
    for type in MARK_TYPES:  #сравнениваем человека и регулярки
        current_iou = []
        for i in range(N - M):
            mark1_filtered = []                         # - список с элементами вида: [start, end], таких, что
            for item in mark1[i][2]:  # тип соответсвующей метки == type
                if type == item[2]:
                    mark1_filtered.append([item[0], item[1]])
            mark2_filtered = []
            for item in mark2[i][2]:
                if type == item[2]:         # аналогично mark2
                    mark2_filtered.append([item[0], item[1]])
            mark1_filtered.sort(key=lambda x: x[0])
            mark2_filtered.sort(key=lambda x: x[0])

            for j in range(abs(len(mark1_filtered) - len(mark2_filtered))): # за разницу между колличеством меток накидываем нулевых метрик
                current_iou.append(0.0)

            if (len(mark1_filtered) == 0) or (len (mark2_filtered) == 0):
                continue
                
            while (len(mark1_filtered) > len(mark2_filtered)):  # пока не исправим разницу удаляем лишние элементы
                if(mark1_filtered[0][1] > mark2_filtered[0][0]): # если конец 1 элемента бОльшего списка правее, чем начало 1 элемента меньшего то удаляем последний элемент бОльшего списка
                    mark1_filtered.pop()
                else:               # иначе первый
                    mark1_filtered.pop(0)
            while (len(mark2_filtered) > len(mark1_filtered)):
                if(mark2_filtered[0][1] > mark1_filtered[0][0]):
                    mark2_filtered.pop()
                else:
                    mark2_filtered.pop(0)
            # cравняли списки
            for j in range(len(mark1_filtered)):
                current_iou.append(iou(mark1_filtered[j], mark2_filtered[j]))
        if len(current_iou) != 0:
            avr_iou[type] = sum(current_iou) / len(current_iou)
            iou_count[type] = sum([1 for l in current_iou if l >= THRESHOLD])
        else:
            avr_iou[type] = 0
            iou_count[type] = 0
    return avr_iou, iou_count

    
    


def main():

    print(f"From {M} to {N}")
    print(f"IoU threshold: {THRESHOLD}\tMax IoU count: {N - M}")

    regex_marks = input_regex()

    human_marks = input_marked_data("annotations")

    avr_iou, iou_count = compare_marks(human_marks, regex_marks)
    
    
    print()
    print(f"{"Mark":^17} {"Avr IoU":^20} {"IoU count":^9}")
    for type in MARK_TYPES:
        print(f"{type+':':<17} {avr_iou[type]:<20} {iou_count[type]:^9}")
    print()




if __name__ == "__main__":
    main()
