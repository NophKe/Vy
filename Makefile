all: syntax.so screen.so

syntax.c: syntax.pyx
	python -m cython -3 syntax.pyx
syntax.so: syntax.c
	gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm -o syntax.so syntax.c

screen.c: screen.py
	python -m cython -3 screen.py
screen.so: screen.c
	gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm -o screen.so screen.c

