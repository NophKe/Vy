all: console.so screen.so 

console.c: console.pyx
	cythonize3 -3 console.pyx
console.so: console.c
	gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm -o console.so console.c

screen.c: screen.pyx
	cythonize3 -3 screen.pyx
screen.so: screen.c
	gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm -o screen.so screen.c

