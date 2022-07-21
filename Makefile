all: top_level filetypes_module interface_module

filetypes_module: filetypes/basefile.so \
				  filetypes/textfile.so \
				  filetypes/__init__.so
top_level: actions.so \
           keys.so \
		   global_config.so \
		   editor.so \
		   screen.so \
		   console.so 
interface_module: interface/__init__.so \
                  interface/insert.so  \
				  interface/command.so \
				  interface/python.so \
				  interface/helpers.so

filetypes/textfile.so: filetypes/basefile.so
action.so: editor.so
editor.so: screen.so console.so
screen.so: filetypes/textfile.so
interface/command.so: filetypes/basefile.so screen.so editor.so interface/helpers.so
interface/normal.so: editor.so 
interface/insert.so: interface/helpers.so editor.so


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

CC  = gcc --shared -s -I/usr/include/python3.10 -march=native -mtune=native -O3 -pipe -fPIC -Wall -L/usr/lib
#CC  = gcc --shared -s -I/usr/include/python3.10 -march=native -mtune=native -O3 -pipe -fPIC -Wall -L/usr/lib -lcrypt -ldl -lutil -lm
#CC = gcc --shared  -fopenacc                  -s  -I/usr/include/python3.10                -march=native -mtune=native -O3 -pipe                                      -fPIC         -Wall -L/usr/lib -lcrypt           -ldl -lutil -lm
#CC = gcc --shared  -ftree-parallelize-loops=8 -s  -I/usr/include/python3.10                -march=native -mtune=native -O3 -pipe                                      -fPIC         -Wall -L/usr/lib -lcrypt           -ldl -lutil -lm
#CC = gcc --shared                             -s -I/usr/include/python3.10                -march=native -mtune=native -Os -pipe                                      -fPIC         -Wall -L/usr/lib -lcrypt           -ldl -lutil -lm
#CC = gcc --shared                             -s -I/usr/include/python3.10 -Wsign-compare -march=native -mtune=native -O3 -pipe -fno-plt -fno-semantic-interposition -fPIC -fwrapv -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm
#CC = gcc --shared                                 -I/usr/include/python3.10 -Wsign-compare -march=native -mtune=native -O3 -pipe -fno-plt -fno-semantic-interposition -fPIC -fwrapv -Wall -L/usr/lib -lcrypt -lpthread -ldl -lutil -lm
#CC="gcc --shared  $(shell python-config --includes) $(shell python-config --libs) $(shell python-config --cflags) $(shell python-config --ldflags)"

gcc-config:
	echo ${CC}

%.so: %.c %.py %.pxd
	${CC} $< -o $@

%.c: %.py %.pxd
	cython --fast-fail -Wextra -X warn.unused_result=True -X warn.undeclared=True -X infer_types=True -a -3 $<
# cython --fast-fail -a -3 $<
#	cython -Werror --fast-fail -Wextra -a -3 -X warn.undeclared=True $<
#	cythonize -a -3 $<
