/* Count Python object allocations (PYMEM_DOMAIN_OBJ).
 *
 * Small objects never reach libc malloc, so an LD_PRELOAD counter misses
 * the tuples and lists these parsers allocate. This wraps the object
 * allocator and keeps the original free, so objects allocated before the
 * module was imported are still released safely.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyMemAllocatorEx orig_alloc;
static unsigned long long alloc_count;

static void *
counting_malloc(void *ctx, size_t size)
{
    alloc_count++;
    return orig_alloc.malloc(ctx, size);
}

static void *
counting_calloc(void *ctx, size_t nelem, size_t elsize)
{
    alloc_count++;
    return orig_alloc.calloc(ctx, nelem, elsize);
}

static void *
counting_realloc(void *ctx, void *ptr, size_t new_size)
{
    alloc_count++;
    return orig_alloc.realloc(ctx, ptr, new_size);
}

static void
counting_free(void *ctx, void *ptr)
{
    orig_alloc.free(ctx, ptr);
}

static PyObject *
reset_count(PyObject *self, PyObject *args)
{
    alloc_count = 0;
    Py_RETURN_NONE;
}

static PyObject *
get_count(PyObject *self, PyObject *args)
{
    return PyLong_FromUnsignedLongLong(alloc_count);
}

static PyMethodDef methods[] = {
    {"reset", reset_count, METH_NOARGS, 0},
    {"get", get_count, METH_NOARGS, 0},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "countalloc",
    "Count PYMEM_DOMAIN_OBJ allocations.",
    -1,
    methods
};

PyMODINIT_FUNC
PyInit_countalloc(void)
{
    PyMemAllocatorEx wrapped;

    PyMem_GetAllocator(PYMEM_DOMAIN_OBJ, &orig_alloc);
    wrapped.ctx = NULL;
    wrapped.malloc = counting_malloc;
    wrapped.calloc = counting_calloc;
    wrapped.realloc = counting_realloc;
    wrapped.free = counting_free;
    PyMem_SetAllocator(PYMEM_DOMAIN_OBJ, &wrapped);
    return PyModule_Create(&moduledef);
}
