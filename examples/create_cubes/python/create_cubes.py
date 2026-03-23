#! /usr/bin/env python3

from pxr import Usd, Gf, UsdGeom

def create_hierarchical_cubes(filename):
    # Create a new stage to hold the scene
    stage = Usd.Stage.CreateNew(filename)
    
    # Define the base path for the cube
    base_path = '/Cube1'
    
    # Create the first cube
    cube1 = UsdGeom.Cube.Define(stage, base_path)
    cube1.GetSizeAttr().Set(1)
    # No need to move the first cube, it's the root

    # Create the second cube as a child of the first
    cube2 = UsdGeom.Cube.Define(stage, f'{base_path}/Cube2')
    cube2.GetSizeAttr().Set(0.5)
    xform = UsdGeom.Xformable(stage.GetPrimAtPath( f'{base_path}/Cube2'))
    translate_op = xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3f(0, 0.5+0.25+0.1, 0)) # relative from parent
    
    # Create the third cube as a child of the second
    cube3 = UsdGeom.Cube.Define(stage, f'{base_path}/Cube2/Cube3')
    cube3.GetSizeAttr().Set(0.25)
    xform = UsdGeom.Xformable(stage.GetPrimAtPath( f'{base_path}/Cube2/Cube3'))
    translate_op = xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3f(0, 0.25+0.1+0.125, 0)) # relative from parent

    # Save the stage to a USD file
    stage.GetRootLayer().Save()

if __name__ == "__main__":
    # Specify the name of the file to save the USD scene
    filename = 'cubes.usda'
    create_hierarchical_cubes(filename)
    # usdview ./cubes.usda