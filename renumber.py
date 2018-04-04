#!/usr/bin/python3
import fileinput
import re

# Ignore mem-00-header.xml and mem-28-footer.xml because they don't contain entries.
filenames = ['mem-01-b.xml', 'mem-02-ch.xml', 'mem-03-D.xml', 'mem-04-gh.xml', 'mem-05-H.xml', 'mem-06-j.xml', 'mem-07-l.xml', 'mem-08-m.xml', 'mem-09-n.xml', 'mem-10-ng.xml', 'mem-11-p.xml', 'mem-12-q.xml', 'mem-13-Q.xml', 'mem-14-r.xml', 'mem-15-S.xml', 'mem-16-t.xml', 'mem-17-tlh.xml', 'mem-18-v.xml', 'mem-19-w.xml', 'mem-20-y.xml', 'mem-21-a.xml', 'mem-22-e.xml', 'mem-23-I.xml', 'mem-24-o.xml', 'mem-25-u.xml', 'mem-26-suffixes.xml', 'mem-27-extra.xml']
java_filename = '../app/src/main/java/org/tlhInganHol/android/klingonassistant/KlingonContentDatabase.java'

# Renumber all the "_id" fields, starting at 10000 for the first entry, and incrementing by 1 for each entry.
id = 10000;
for filename in filenames:
    # Keep track of the ID of the first entry in the "extra" section.
    if filename == 'mem-27-extra.xml':
        max_id_plus_one = id;
    with fileinput.FileInput(filename, inplace=True) as file:
        for line in file:
            (line, num_subs) = re.subn(r"_id\">(\d*)<", "_id\">%s<" % id, line)
            print(line, end='')
            if num_subs != 0:
                id += 1

# Write the ID of the first entry in the "extra" section to the "EXTRA" file and the KlingonContentDatabase.java file.
extra_file = open("EXTRA", "w")
extra_file.write(str(max_id_plus_one))
extra_file.close()
try:
    with fileinput.FileInput(java_filename, inplace=True) as java_file:
        for line in java_file:
            (line, num_subs) = re.subn(r"ID_OF_FIRST_EXTRA_ENTRY = (\d*);", "ID_OF_FIRST_EXTRA_ENTRY = %s;" % max_id_plus_one, line)
            print(line, end='')
except IOError:
    print("Warning: KlingonContentDatabase.java not updated.")
