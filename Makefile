all: screen.so console.so action.so interface/normal_mode.so


CC = gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm

%.so:
	${CC} -o $< $@

.c: 
	python -m cython -3 $<

#console.c: console.py
#	python -m cython -3 console.py
#console.so: console.c
#	${CC} -o console.so console.c
#
#screen.c: screen.py
#	python -m cython -3 screen.py
#screen.so: screen.c
#	${CC} -o screen.so screen.c

