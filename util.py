import csv

def write_line(path, line):
    f = open(path, "a+")
    f.write(line)
    f.close()

def write_csv(path, list):
    with open(path, 'a+') as file:
        writer = csv.writer(file)
        writer.writerows([list])
