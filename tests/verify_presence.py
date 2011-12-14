import re
import sys

if __name__ == "__main__":
    """Returns zero if and only if the string sys.argv[2] does not occur in the
       file sys.argv[1]"""

    assert re.search('value="nan"', '    <event date="2011-10-01" flag="0" time="23:00:00" value="nan"/>') is not None

    file_path, search_string = tuple(sys.argv[1:3])
    print "Searching for occurrence of \'%s\' in file \'%s\'" % (search_string, file_path)
    line_nr = 1
    f = open(file_path)
    for line in f:
        if re.search(search_string, line) is not None:
            print 'First occurrence found at line %d' % line_nr
            exit(1)
        line_nr += 1
    print 'No occurrence found'
    exit(0)


