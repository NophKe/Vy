all: top_level subdirs

subdirs: filetypes_module

filetypes_module:
	$(MAKE) -C filetypes

top_level: keys.so editor.so screen.so
editor.so: filetypes_module screen.so

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

CC  = gcc --shared -s -I/usr/include/python3.11 -march=native -mtune=native -O3 -pipe -fPIC -Wall -L/usr/lib
gcc-config:
	echo ${CC}

%.so: %.c %.py %.pxd
	${CC} $< -o $@

.PRECIOUS: %.c

%.c: %.py %.pxd
	cython --fast-fail -Wextra -X infer_types=True -a -3 $<
	#cython --fast-fail -Wextra -X warn.undeclared=True -X infer_types=True -a -3 $<
	#cython --fast-fail -Wextra -X warn.unused_result=True -X warn.undeclared=True -X infer_types=True -a -3 $<
