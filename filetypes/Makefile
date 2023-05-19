all: __init__.so

__init__.so: textfile.so basefile.so

textfile.so: basefile.so lexer.so

CC  = gcc --shared -s -I/usr/include/python3.11 -march=native -mtune=native -O3 -pipe -fPIC -Wall -L/usr/lib
%.so: %.c %.py %.pxd
	${CC} $< -o $@

%.c: %.py %.pxd
	cython --fast-fail -Wextra -X infer_types=True -a -3 $<
	

