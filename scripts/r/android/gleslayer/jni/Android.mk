LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE     := libGLES_glesLayer
LOCAL_SRC_FILES  := ../glesLayer.cpp
LOCAL_CPPFLAGS   += -std=c++14
LOCAL_LDLIBS     += -llog

include $(BUILD_SHARED_LIBRARY)
