# Building with clang 20 & clang std

- the following can compile, but has errors when running usdview
- explicitly forcing Clang to use LLVM's C++ standard library (libc++)
- the Python interpreter your build is linking against: x86_64-linux-gnu/libpython3.12.so
  - .local/share/uv/python/cpython-3.12.13-linux-x86_64-gnu
- the system's Python was built using GCC and GNU's C++ standard library (libstdc++).

```sh
python3 ./build_scripts/build_usd.py \
    -v \
    --vulkan --no-examples --no-tutorials \
    --cmake-build-args "-DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_CXX_FLAGS='-stdlib=libc++' -DCMAKE_EXE_LINKER_FLAGS='-stdlib=libc++' -DCMAKE_SHARED_LINKER_FLAGS='-stdlib=libc++'" \
    ./build
```

Starting usdview resulted in the following error:

```
State file not found, a new one will be created.
Traceback (most recent call last):
  File "/home/developer/OpenUSD/OpenUSD/build/bin/usdview", line 18, in <module>
    Usdviewq.Launcher().Run()
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/__init__.py", line 79, in Run
    app, appController = self.LaunchPreamble(arg_parse_result)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/__init__.py", line 417, in LaunchPreamble
    appController = AppController(arg_parse_result, contextCreator)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/appController.py", line 562, in __init__
    self._resetSettings()
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/appController.py", line 2490, in _resetSettings
    self._reloadVaryingUI()
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/appController.py", line 1862, in _reloadVaryingUI
    self._stageView = StageView(
                      ^^^^^^^^^^
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/stageView.py", line 865, in __init__
    self._dataModel.viewSettings.freeCamera = self._createNewFreeCamera(
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/stageView.py", line 1124, in _createNewFreeCamera
    return FreeCamera(
           ^^^^^^^^^^^
  File "/home/developer/OpenUSD/OpenUSD/build/lib/python/pxr/Usdviewq/freeCamera.py", line 44, in __init__
    aspectRatio, fov, Gf.Camera.FOVVertical)
                      ^^^^^^^^^^^^^^^^^^^^^
AttributeError: type object 'Camera' has no attribute 'FOVVertical'
```