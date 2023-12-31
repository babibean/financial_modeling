## This script is intended to show procesing times for reading/writing to files using pytables
## Taken from chapter 9, pages 252 - 267 of Reference book
import time
import numpy as np
from pylab import plt
import tables as tb 
import datetime as dt
import numexpr as ne

path = '../data/'
filename = path + 'pytab.h5'

# create and open new file using tables package
h5 = tb.open_file(filename, 'w')

# describe each row and datatype
row_des = {
'Date': tb.StringCol(26, pos=1),
'No1': tb.IntCol(pos=2), 
'No2': tb.IntCol(pos=3), 
'No3': tb.Float64Col(pos=4), 
'No4': tb.Float64Col(pos=5) }

rows = 2000000

# use filters to describe compression
filters = tb.Filters(complevel=0)

# create new table
tab = h5.create_table('/', 'ints_floats', row_des,
                                    title='Integers and Floats',
                                    expectedrows=rows,
                                    filters=filters)

# create pointer object
pointer = tab.row

# create random value numpy arrays - one of integers and one of floats
ran_int = np.random.randint(0, 10000, size=(rows, 2)) 
ran_flo = np.random.standard_normal((rows, 2)).round(4)

# iterate through each row to define data
t1 = time.time()
for i in range(rows):
    pointer['Date'] = dt.datetime.now() 
    pointer['No1'] = ran_int[i, 0] 
    pointer['No2'] = ran_int[i, 1] 
    pointer['No3'] = ran_flo[i, 0] 
    pointer['No4'] = ran_flo[i, 1] 
    pointer.append()
# flush data -write it to file
tab.flush()
t2 = time.time()
print("Time to write to pointer (using for loop): {} secs\n".format(t2-t1))

# define new numpy array of datatypes, then use it to initiate a zeros array
dty = np.dtype([('Date', 'S26'), ('No1', '<i4'), ('No2', '<i4'), ('No3', '<f8'), ('No4', '<f8')])
sarray = np.zeros(len(ran_int), dtype=dty)

# time how long it takes to define data in array
t1 = time.time()
sarray['Date'] = dt.datetime.now() 
sarray['No1'] = ran_int[:, 0] 
sarray['No2'] = ran_int[:, 1] 
sarray['No3'] = ran_flo[:, 0] 
sarray['No4'] = ran_flo[:, 1]
t2 = time.time()
print("Time to write to pointer (direct definition): {} secs\n".format(t2-t1))

# create table & populate with data
h5.create_table('/', 'ints_floats_from_array', sarray,
                      title='Integers and Floats',
                    expectedrows=rows, filters=filters)

# remove second table object that has redundant data
h5.remove_node('/', 'ints_floats_from_array')


# create query like used with SQL databases:
query = '((No3 < -0.5) | (No3 > 0.5)) & ((No4 < -1) | (No4 > 1))'
iterator = tab.where(query)
t1 =time.time()
res = [(row['No3'], row['No4']) for row in iterator]
t2 = time.time()
print("Time to read data from iterator object that's based on query: {} secs\n".format(t2-t1))


# time how long to get stats for data
t1 = time.time()
values = tab[:]['No3']
t2 = time.time()
print('Max %18.3f' % values.max())
print('Ave %18.3f' % values.mean()) 
print('Min %18.3f' % values.min()) 
print('Std %18.3f' % values.std())
print("Time to get column from data: {} secs\n".format(t2-t1))

# time how long to get stats from query
t1 = time.time()
res = [(row['No1'], row['No2']) for row in
tab.where('((No1 > 9800) | (No1 < 200)) & ((No2 > 4500) & (No2 < 5500))')]
t2 = time.time()
print("Time to filter within data: {} secs\n".format(t2-t1))


### Working with compressed data:

filename = path + 'pytabc.h5'

# create and open new h5 file
h5c = tb.open_file(filename, 'w') 

# define how much compression to add
filters = tb.Filters(complevel=5, complib='blosc')

# create table
tabc = h5c.create_table('/', 'ints_floats', sarray, title='Integers and Floats',
expectedrows=rows, filters=filters) 

# define new query
query = '((No3 < -0.5) | (No3 > 0.5)) & ((No4 < -1) | (No4 > 1))'
# and create iterator object based upon it
iteratorc = tabc.where(query)

# Time how long it takes to iterate through compressed iterator
t1 = time.time()
res = [(row['No3'], row['No4']) for row in iteratorc]
t2 = time.time()
print("Time to read data from iterator object (compressed dataset): {} secs\n".format(t2-t1))

# Time how long it takes to read non-compressed dataset, as well as print stats on file size & array size
t1 = time.time()
arr_non = tab.read()
t2 = time.time()
print("Time to read data from regular (noncompressed) table: {} secs".format(t2-t1))
print("File size of table: {}".format(tab.size_on_disk))
print("size of array in python: {}\n".format(arr_non.nbytes))

# do the same for compressed dataset- time how long it takes to read in, and print storage stats
t1 = time.time()
arr_com = tabc.read()
t2 = time.time()
print("Time to read data from compressed table: {} secs".format(t2-t1))
print("File size of table: {}".format(tabc.size_on_disk))
print("size of array in python: {}\n".format(arr_com.nbytes))

# close out compressed file
h5c.close()

# Store data from ints array & floats array
arr_int = h5.create_array('/', 'integers', ran_int) 
arr_flo = h5.create_array('/', 'floats', ran_flo)

# close out connection
h5.close()

### Test out out-of-memory creation
filename = path + 'earray.h5' 
h5 = tb.open_file(filename, 'w')

n = 500

# create EArray object
ear = h5.create_earray('/', 'ear', atom=tb.Float64Atom(),shape=(0, n))

# create large random matrix
rand = np.random.standard_normal((n, n))

# time how long it takes to append large matrix over many times
t1 = time.time()
for _ in range(750):
    ear.append(rand) 
ear.flush()
t2 = time.time()
print("Time to write data to earray: {} secs".format(t2-t1))

print("Size of earray array on disk: {}\n".format(ear.size_on_disk))

# test out creating an EArray object using a mathematical equation
out = h5.create_earray('/', 'out', atom=tb.Float64Atom(),shape=(0, n))
print("Size of 'out' earray array on disk after creation: {}\n".format(out.size_on_disk))

#Transform a str object–based expression to an Expr object
expr = tb.Expr('3 * sin(ear) + sqrt(abs(ear))') 

# Defines the output to be the out EArray object
expr.set_output(out, append_mode=True)

#Initiate the evaluation of the expression
t1 = time.time()
expr.eval()
t2 = time.time()
print("Time to evalulate expression for 'out' EArray: {} secs".format(t2-t1))
print("Size of 'out' earray array on disk after evaluating expression: {}\n".format(out.size_on_disk))

# read entire EArray into memory
t1 = time.time()
out_ = out.read()
t2 =time.time()
print("Time to read entire Earray 'out' into memory: {} secs\n".format(t2-t1))


## Now compare to numexpr module to compare performance:
expr = '3 * sin(out_) + sqrt(abs(out_))'

# initially set to use 1 thread
ne.set_num_threads(1)

t1 = time.time()
ne.evaluate(expr)[0, :10]
t2 = time.time()
print("Time to evaulate expression on EArray with numexpr, 1 thread: {} secs".format(t2-t1))

# now set to use 4 threads
ne.set_num_threads(4)

t1 = time.time()
ne.evaluate(expr)[0, :10]
t2 = time.time()
print("Time to evaulate expression on EArray with numexpr, 4 threads: {} secs".format(t2-t1))

# close out h5 connection
h5.close()