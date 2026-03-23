#! /usr/bin/env python3

from pxr import Usd, Gf, UsdGeom, Sdf
import time
import math

def update_cube3_position(new_filename: str, time_step: int) -> None:
    # Open an existing USD stage and also create a session layer within the stage
    stage: Usd.Stage = Usd.Stage.Open('cubes.usda')
    
    # Use the session layer that already exists in the stage
    session_layer: Sdf.Layer = stage.GetSessionLayer()
    
    # Set the session layer as the current edit target
    stage.SetEditTarget(session_layer)
    
    # Fetch the Xformable prim at the path of Cube2
    cube3_path: str = '/Cube1/Cube2'
    xform: UsdGeom.Xformable = UsdGeom.Xformable(stage.GetPrimAtPath(cube3_path))
    if not xform:
        raise Exception(f"No Cube2 found at path: {cube3_path}")
    
    # Set the translation attribute directly
    translate_op: UsdGeom.XformOp = xform.GetTranslateOp()
    current_pos: Gf.Vec3d = translate_op.Get()
    new_pos: Gf.Vec3d = current_pos + Gf.Vec3d(0, math.sin(float(time_step))/15, 0)
    translate_op.Set(new_pos)
    
    # Save changes to a new file from the session layer
    session_layer.Export(new_filename)

def main():
    new_filename: str = 'cubes_session_layer.usda'
    
    # Example of updating the cube position
    for i in range(1000):
        dt: float = 1.0/60
        update_cube3_position(new_filename, i*dt)
        time.sleep(dt)

if __name__ == "__main__":
    main()
    # usdview --sessionLayer ./cubes_session_layer.usda  ./cubes.usda