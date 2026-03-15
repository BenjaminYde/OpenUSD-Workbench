# configure cmake version
cmake_minimum_required(VERSION 3.31 FATAL_ERROR)
project(create_cubes CXX)

# cmake include modules
include(FetchContent)

# create target
set(TARGET_NAME MyTarget)

# create executable
add_executable(${TARGET_NAME} main.cpp)

if(NOT TARGET Vulkan::shaderc_combined)
    add_library(Vulkan::shaderc_combined INTERFACE IMPORTED)
endif()

# find packages: openusd dependencies
find_package(OpenGL REQUIRED)
find_package(X11 REQUIRED)
find_package(Vulkan REQUIRED)

# find packages: openusd
find_package(pxr REQUIRED)

# include directories
target_include_directories(${TARGET_NAME} PRIVATE ${PXR_INCLUDE_DIRS})
target_link_libraries(${TARGET_NAME} PRIVATE ${PXR_LIBRARIES})