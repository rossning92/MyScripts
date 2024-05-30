// https://android.googlesource.com/platform/cts/+/master/hostsidetests/gputools/layers/jni/glesLayer.cpp

#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <android/log.h>
#include <cstring>
#include <string.h>
#include <string>
#include <unordered_map>

#define xstr(a) str(a)
#define str(a) #a
#define LOG_TAG "glesLayer"
#define ALOGI(msg, ...)                                                        \
  __android_log_print(ANDROID_LOG_INFO, LOG_TAG, (msg), __VA_ARGS__)
class StaticLogMessage {
public:
  StaticLogMessage(const char *msg) { ALOGI("%s", msg); }
};
StaticLogMessage g_initMessage("glesLayer loaded");
typedef __eglMustCastToProperFunctionPointerType EGLFuncPointer;
typedef void *(*PFNEGLGETNEXTLAYERPROCADDRESSPROC)(void *, const char *);
namespace {
std::unordered_map<std::string, EGLFuncPointer> funcMap;

EGLAPI EGLDisplay EGLAPIENTRY glesLayer_glViewport(GLint x, GLint y,
                                                   GLsizei width,
                                                   GLsizei height) {
  ALOGI("glesLayer_glViewport called with parameters: %d %d %d %d", x, y, width,
        height);
  if (funcMap.find("glViewport") == funcMap.end())
    ALOGI("%s", "Unable to find funcMap entry for glViewport");
  EGLFuncPointer entry = funcMap["glViewport"];
  typedef EGLDisplay (*PFNGLVIEWPORTPROC)(GLint, GLint, GLsizei, GLsizei);
  PFNGLVIEWPORTPROC next = reinterpret_cast<PFNGLVIEWPORTPROC>(entry);
  return next(x, y, width, height);
}

EGLAPI EGLFuncPointer EGLAPIENTRY eglGPA(const char *funcName) {
#define GETPROCADDR(func)                                                      \
  if (!strcmp(funcName, #func)) {                                              \
    ALOGI("%s%s%s", "Returning glesLayer_" #func " for ", funcName,            \
          " in eglGPA");                                                       \
    return (EGLFuncPointer)glesLayer_##func;                                   \
  }
  GETPROCADDR(glViewport);
  // Don't return anything for unrecognized functions
  return nullptr;
}

EGLAPI void EGLAPIENTRY glesLayer_InitializeLayer(
    void *layer_id,
    PFNEGLGETNEXTLAYERPROCADDRESSPROC get_next_layer_proc_address) {
  ALOGI("%s%llu%s%llu", "glesLayer_InitializeLayer called with layer_id (",
        (unsigned long long)layer_id, ") get_next_layer_proc_address (",
        (unsigned long long)get_next_layer_proc_address);
  // Pick a real function to look up and test the pointer we've been handed
  const char *func = "eglGetProcAddress";
  ALOGI("%s%s%s%llu%s%llu%s", "Looking up address of ", func,
        " using get_next_layer_proc_address (",
        (unsigned long long)get_next_layer_proc_address, ") with layer_id (",
        (unsigned long long)layer_id, ")");
  void *gpa = get_next_layer_proc_address(layer_id, func);
  // Pick a fake function to look up and test the pointer we've been handed
  func = "eglFoo";
  ALOGI("%s%s%s%llu%s%llu%s", "Looking up address of ", func,
        " using get_next_layer_proc_address (",
        (unsigned long long)get_next_layer_proc_address, ") with layer_id (",
        (unsigned long long)layer_id, ")");
  gpa = get_next_layer_proc_address(layer_id, func);
  ALOGI("%s%llu%s%s", "Got back (", (unsigned long long)gpa, ") for ", func);
}
EGLAPI EGLFuncPointer EGLAPIENTRY
glesLayer_GetLayerProcAddress(const char *funcName, EGLFuncPointer next) {
  EGLFuncPointer entry = eglGPA(funcName);
  if (entry != nullptr) {
    ALOGI("%s%s%s%llu%s", "Setting up glesLayer version of ", funcName,
          " calling down with: next (", (unsigned long long)next, ")");
    funcMap[std::string(funcName)] = next;
    return entry;
  }
  // If the layer does not intercept the function, just return original func
  // pointer
  return next;
}
} // namespace

extern "C" {
__attribute((visibility("default"))) EGLAPI void AndroidGLESLayer_Initialize(
    void *layer_id,
    PFNEGLGETNEXTLAYERPROCADDRESSPROC get_next_layer_proc_address) {
  return (void)glesLayer_InitializeLayer(layer_id, get_next_layer_proc_address);
}

__attribute((visibility("default"))) EGLAPI void *
AndroidGLESLayer_GetProcAddress(const char *funcName, EGLFuncPointer next) {
  return (void *)glesLayer_GetLayerProcAddress(funcName, next);
}
}