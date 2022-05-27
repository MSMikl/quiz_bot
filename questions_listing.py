import json
import os

files_index = []


def question_read(file):
    question = {}
    splitted_text = file.read().split('\n\n')
    for element in splitted_text:
        key = element.split('\n')[0].split(' ')[0].lower().replace(':', '')
        if key:
            question[key] = ' '.join(element.split('\n')[1:])
    return question


with open(
    os.path.join(os.path.curdir, 'questions', 'index'),
    'r',
    encoding="KOI8-R"
) as file:
    for line in file:
        filename = line.split()[0]
        if len (filename.split('.')) > 1:
            files_index.append(filename)

print(files_index)

questions = {}

for filename in files_index:
    with open(
        os.path.join(os.path.curdir, 'questions', filename),
        'r',
        encoding='KOI8-R'
    ) as file:
        questions[filename] = question_read(file)

with open(
    os.path.join(os.path.curdir, 'questions', 'questions.json'),
    'w',
    encoding='KOI8-R'
) as file:
    json.dump(questions, file, indent=4)
