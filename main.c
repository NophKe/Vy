#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>

// int Py_Main(int argc, wchar_t **argv)
// int Py_BytesMain(argc, argv);

int start_by_import(int argc, char **argv){
	// if we start on that path all signals / threading should
	// be moved here as a rewrite of __main__.py ...
	
	// or maybe compile __main__.py to python bytecode ?

    Py_Initialize();

	PyObject* editor_module = PyImport_ImportModule("vy.editor");
    PyObject* module_dict = PyModule_GetDict(editor_module);
	PyObject* main_loop = PyDict_GetItemString(module_dict, "_Editor");
    PyObject_CallNoArgs(PyObject_CallNoArgs(main_loop));
	return 0;
	}

int main(int argc, char** argv){
    FILE* main_script = fopen("__main__.py", "r");
	Py_Initialize();
//	PyRun_AnyFile(main_script, "__main__.py");
	PyRun_SimpleFile(main_script, "__main__.py");
	return 0;
}
