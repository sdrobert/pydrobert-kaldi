'''Sanity check to make sure tables allocate and deallocate'''

from __future__ import division
from __future__ import print_function

from tempfile import NamedTemporaryFile

import numpy

from memory_profiler import profile
from pydrobert.kaldi import tables

@profile
def main():
    temp = NamedTemporaryFile()
    
    writer = tables.open('ark:{}'.format(temp.name), 'fv', mode='w')
    for key in range(1000):
        val = numpy.random.random(
            numpy.random.randint(1, 10000)
        ).astype(numpy.float32)
        writer.write(str(key), val)
        del val
    del writer

    reader = tables.open('ark:{}'.format(temp.name), 'fv', mode='r')
    num = 0
    for val in iter(reader):
        num += 1
    assert num == 1000
    del reader

    reader = tables.open('ark:{}'.format(temp.name), 'fv', mode='r+')
    for _ in range(50):
        key = str(numpy.random.randint(999))
        val = reader[key]
        del val
    del reader

    del temp

if __name__ == '__main__':
    main()
