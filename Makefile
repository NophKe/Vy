all: top_level filetypes_module interface_module

filetypes_module: filetypes/basefile.so filetypes/textfile.so filetypes/__init__.so
top_level: actions.so keys.so global_config.so editor.so screen.so console.so 
interface_module: top_level interface/__init__.so interface/insert.so interface/command.so interface/python.so


action.so: editor.so
editor.so: screen.so console.so
screen.so: filetypes/textfile.so

clean:
	rm -f ./*.c
	rm -f ./*.o
	rm -f ./*.so
	rm -f ./*.html
	####
	rm -f filetypes/*.c
	rm -f filetypes/*.html
	rm -f filetypes/*.o
	rm -f filetypes/*.so
	####
	rm -f interface/*.c
	rm -f interface/*.html
	rm -f interface/*.o
	rm -f interface/*.so
	####
	rm -Rf filetypes/__pycache__/
	rm -Rf interface/__pycache__/
	rm -Rf ./__pycache__/

#CC = gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=x86-64 -mtune=generic -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm

CC = gcc --shared -fPIC -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -I/usr/include/python3.9 -Wno-unused-result -Wsign-compare -march=native -mtune=native -O3 -pipe -fno-plt -fno-semantic-interposition -DNDEBUG -g -fwrapv -O3 -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm -lm

%.so: %.c
	${CC} $< -o $@

%.c: %.py %.pxd
	cythonize -a -3 $<

