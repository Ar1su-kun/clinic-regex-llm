import json
import re
from itertools import permutations

N = 200
M = 0
THRESHOLD = 0.5

MARK_TYPES = ["СилаРекомендации", "Цель", "Состояние", "Популяция", "Действие", "Модификатор"]


with open('import_clear.json', 'r', encoding='utf-8') as json_file:
    NOT_MARKED_DATA = json.load(json_file)
with open('REGEX.json', 'r', encoding='utf-8') as json_file:
    REGEX= json.load(json_file)
with open('import_with_annotations.json', 'r', encoding='utf-8') as json_file:
    MARKED_DATA = json.load(json_file)


class Span:

    _type_strength = ["СилаРекомендации", "Цель", "Состояние", "Популяция", "Действие", "Модификатор"]

    def __init__(self, start: int, end: int, type: str, text: str):
        self.start = start
        self.end = end
        self.type = type
        self.text = text
        if self.end - self.start != len(self.text):
            print(self.text, self.start, self.end)
            raise Exception("Span has inappropriate borders and text")

    def __str__(self):
        return f"{self.text}"
    
    def __len__(self):
        return len(self.text)
    
    def get_rank(self) -> int:
        return self._type_strength.index(self.type)
    
    def __eq__(self, other):
        if not isinstance(other, Span):
            return NotImplemented
        return (self.start == other.start) and (self.end == other.end) and (self.type == other.type) and (self.text == other.text)
    
    def __gt__(self, other):
        if not isinstance(other, Span):
            raise ValueError("Argument must be a span")
        return self.get_rank() > other.get_rank()
    
    def __lt__(self, other):
        if not isinstance(other, Span):
            raise ValueError("Argument must be a span")
        return self.get_rank() < other.get_rank()
    
    def __ge__(self, other):
        if not isinstance(other, Span):
            raise ValueError("Argument must be a span")
        return self.get_rank() >= other.get_rank()
    
    def __le__(self, other):
        if not isinstance(other, Span):
            raise ValueError("Argument must be a span")
        return self.get_rank() <= other.get_rank()
    
    def __contains__(self, other): #in
        if not isinstance(other, Span):
            raise ValueError("Argument must be a span")
        return (self.start <= other.start) and (other.end <= self.end)
        
    @staticmethod
    def iou(left, right):
        if not isinstance(left, Span):
            raise ValueError("Left argument must be a span")
        if not isinstance(right, Span):
            raise ValueError("Right argument must be a span")
        
        intersection = max(0, min(left.end, right.end) - max(left.start, right.start))
        union = (left.end - left.start) + (right.end - right.start) - intersection
        if union == 0:
            return 0.0
        return intersection / union
    
    @staticmethod
    def isIntersec(left, right):
        if not isinstance(left, Span):
            raise ValueError("First argument must be a span")
        if not isinstance(right, Span):
            raise ValueError("Second argument must be a span")
        
        intersection = max(0, min(left.end, right.end) - max(left.start, right.start))
        return intersection > 0
        

class Task:
    def __init__(self, id: int, text: str):
        self.id = id
        self.text = text
        self.spans = []

    def add(self, span: Span):
        if not isinstance(span, Span):
            raise ValueError("Argument must be a span")
        self.spans.append(span)

    def remove(self, span: Span):
        if not isinstance(span, Span):
            raise ValueError("Argument must be a span")
        if not span in self.spans:
            raise ValueError("Tasks doesn't house this span")
        self.spans.remove(span)

    def __contains__(self, span: Span):
        if not isinstance(span, Span):
            raise ValueError("Argument must be a span")
        for existing_span in self.spans:
            if ((existing_span.start == span.start) and 
                (existing_span.end == span.end) and 
                (existing_span.type == span.type)):
                return True
        return False

    def __len__(self):
        return len(self.spans)

    def cut(self):
        MINLEN = 2

        # сортируем от более приоритетных к менее
        sorted_spans = sorted(self.spans, key=lambda s: (-s.get_rank(), s.start))

        accepted: list[Span] = []  # уже зафиксированные, непересекающиеся спаны

        for span in sorted_spans:
            fragments: list[Span] = [span]

            for acc in accepted:
                next_fragments = []
                for frag in fragments:
                    if not Span.isIntersec(frag, acc):
                        next_fragments.append(frag)  # нет конфликтов => отправляем на следующую итерацию
                    elif frag.type == acc.type:
                        # Одинаковый тип => объединяем
                        merged_start = min(frag.start, acc.start)
                        merged_end   = max(frag.end,   acc.end)
                        merged_text  = self.text[merged_start:merged_end]
                        accepted.remove(acc)
                        next_fragments.append(Span(merged_start, merged_end, frag.type, merged_text))
                    elif frag in acc: # у acc выше приоритет
                        pass
                    elif acc in frag:
                        if acc.start - frag.start > MINLEN:
                            next_fragments.append(
                                Span(frag.start, acc.start, frag.type,
                                    self.text[frag.start:acc.start]))
                        if frag.end - acc.end > MINLEN:
                            next_fragments.append(
                                Span(acc.end, frag.end, frag.type,
                                    self.text[acc.end:frag.end]))
                    elif frag.start < acc.start:
                        # frag выступает слева => оставляем левый кусок
                        if acc.start - frag.start > MINLEN:
                            next_fragments.append(
                                Span(frag.start, acc.start, frag.type,
                                    self.text[frag.start:acc.start]))
                    else:
                        # frag выступает справа => оставляем правый кусок
                        if frag.end - acc.end > MINLEN:
                            next_fragments.append(
                                Span(acc.end, frag.end, frag.type,
                                    self.text[acc.end:frag.end]))
                fragments = next_fragments

            for frag in fragments:
                if len(frag) > MINLEN:
                    accepted.append(frag)

        newTask = Task(self.id, self.text)
        for span in accepted:
            newTask.add(span)
        return newTask


class Data:
    def __init__(self):
        self.tasks = []

    def add(self, task: Task):
        if not isinstance(task, Task):
            raise ValueError("Argument must be a task")
        self.tasks.append(task)

    def remove(self, task: Task):
        if not isinstance(task, Task):
            raise ValueError("Argument must be a task")
        if not task in self.tasks:
            raise ValueError("Data doesn't house this task")
        self.tasks.remove(task)

    def __len__(self):
        return len(self.tasks)
    
    def cut(self):
        newData = Data()
        for task in self.tasks:
            newData.add(task.cut())
        return newData
    
    def best_strength(self, other):
        if not isinstance(other, Data):
            raise ValueError("Argument must be a data")
        bestperm = []
        bestsum = 0
        for perm in permutations(MARK_TYPES):
            Span._type_strength = perm
            avr_iou, iou_count, total_iou_count = Data.compare_data(self.cut(), other)
            if sum(avr_iou.values()) > bestsum:
                bestsum = sum(avr_iou.values())
                bestperm = perm
        return bestperm
    
    @staticmethod
    def input_marked_data(s:str):
        data = Data()
        for item in MARKED_DATA:
            if (M <= item["data"]["id"] <= N) and item["data"]["id"] != 180:
                task = Task(item["data"]["id"], item["data"]["text"])
                for span1 in item[s][0]["result"]:
                    start = span1["value"]["start"]
                    end = span1["value"]["end"]
                    text = span1["value"]["text"]
                    type = span1["value"]["labels"][0]
                    if(start < 0):
                        continue
                    span = Span(start, end, type, text)
                    task.add(span)
                data.add(task)
        return data
    
    @staticmethod
    def input_regex():
        data = Data()
        for item in NOT_MARKED_DATA:
            if (M <= item["data"]["id"] <= N) and item["data"]["id"] != 180:
                task = Task(item["data"]["id"], item["data"]["text"])
                for type in MARK_TYPES:
                    for match in re.finditer(REGEX[type], task.text):
                        start = match.start()
                        end = match.end()
                        text = match.group()
                        task.add(Span(start, end, type, text))
                data.add(task)
        return data
    
    @staticmethod
    def compare_data(data1, data2):
        avr_iou = {}
        iou_count = {}
        total_iou_count = {}
        if not isinstance(data1, Data):
            raise ValueError("First argument must be a Data")
        if not isinstance(data2, Data):
            raise ValueError("Second argument must be a Data")
        
        for type in MARK_TYPES:
            all_iou = []
            for i in range(len(data1)): #len(data1) == len(data2)
                task1 = data1.tasks[i]
                task2 = data2.tasks[i]

                spans1 = [span for span in task1.spans if span.type == type]
                spans2 = [span for span in task2.spans if span.type == type]

                spans1.sort(key=lambda s: s.start)
                spans2.sort(key=lambda s: s.start)

                s1 = spans1[:] # Копии, чтобы не испортить значения
                s2 = spans2[:] 
                for span1 in s1:
                    best_iou = 0.0
                    best_index = -1
                    for j, span2 in enumerate(s2):
                        cur_iou = Span.iou(span1, span2)
                        if (cur_iou > best_iou):
                            best_iou = cur_iou
                            best_index = j
                        if best_index != -1 and best_iou != 0:
                            all_iou.append(best_iou)
                            del s2[best_index]
                        else:
                            all_iou.append(0.0)
                for s in s2:
                    all_iou.append(0.0)
                
            if len(all_iou) != 0:
                avr_iou[type] = sum(all_iou) / len(all_iou)
                iou_count[type] = sum([1 for iou in all_iou if iou >= THRESHOLD])
                total_iou_count[type] = len(all_iou)
            else:
                avr_iou[type] = 0.0
                iou_count[type] = 0
                total_iou_count[type] = 0
        return avr_iou, iou_count, total_iou_count

    @staticmethod
    def prepare_to_load(predictions, annotaions):
        if not isinstance(predictions, Data):
            raise ValueError("First argument must be a Data")
        if not isinstance(annotaions, Data):
            raise ValueError("Second argument must be a Data")
        load_tasks = []
        for i in range(len(annotaions)):
            pred = []
            for span in predictions.tasks[i].spans:
                pred.append({
                    "from_name": "label",
                    "to_name": "text",
                    "type": "labels",
                    "value": {
                        "start": span.start,
                        "end": span.end,
                        "labels": [span.type],
                        "text": span.text
                    }
                })
            annot = []
            for span in annotaions.tasks[i].spans:
                annot.append({
                    "from_name": "label",
                    "to_name": "text",
                    "type": "labels",
                    "value": {
                        "start": span.start,
                        "end": span.end,
                        "labels": [span.type],
                        "text": span.text
                    }
                })
            pred_result = [{
                "result": pred,
                "score": 0.95
            }]
            annot_result = [{
                "result": annot
            }]
            load_task = {
                "data": {
                    "text": annotaions.tasks[i].text,
                    "id": annotaions.tasks[i].id  
                }
            }
            load_task["predictions"] = pred_result
            load_task["annotations"] = annot_result
            load_tasks.append(load_task)
        with open('load.json', 'w', encoding='utf-8') as load_file:
            json.dump(load_tasks, load_file, ensure_ascii=False, indent=2)



def main():
    print(f"From {M} to {N}")
    print(f"IoU threshold: {THRESHOLD}")
    Span._type_strength = ['Популяция', 'Состояние', 'Модификатор', 'Действие', 'Цель', 'СилаРекомендации']

    human_data = Data.input_marked_data("annotations")

    deepseek_data = Data.input_marked_data("predictions")

    regex_data = Data.input_regex()

    #Span._type_strength = regex_data.best_strength(human_data)

    regex_data = regex_data.cut()

    avr_iou, iou_count, total_iou_count = Data.compare_data(human_data, regex_data)
    

    print()
    print("Human and regex")
    print(f"Span strength: {Span._type_strength}")
    print(f"{"Mark":^17} {"Avr IoU":^20} {"IoU count":^9}")
    for type in MARK_TYPES:
        print(f"{type+':':<17} {avr_iou[type]:<20} {iou_count[type]}/{total_iou_count[type]}")
    Data.prepare_to_load(regex_data, human_data)

    avr_iou, iou_count, total_iou_count = Data.compare_data(human_data, deepseek_data)

    Span._type_strength = ['СилаРекомендации', 'Цель', 'Состояние', 'Популяция', 'Действие', 'Модификатор']
    #Span._type_strength = regex_data.best_strength(deepseek_data)
    print()
    print("Deepseek and regex")
    print(f"Span strength: {Span._type_strength}")
    print(f"{"Mark":^17} {"Avr IoU":^20} {"IoU count":^9}")
    for type in MARK_TYPES:
        print(f"{type+':':<17} {avr_iou[type]:<20} {iou_count[type]}/{total_iou_count[type]}")
    print()
    
    return 0

if __name__ == "__main__":
    main()