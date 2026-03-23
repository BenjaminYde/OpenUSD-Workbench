#! /usr/bin/env python3

from pxr import Usd, Gf, UsdGeom
import time

def create_usd_file(filename: str) -> Usd.Stage:
    # Create a new stage with ASCII format
    stage: Usd.Stage = Usd.Stage.CreateNew(filename)
    
    # Define a Cube primitive at the root layer
    cube: UsdGeom.Cube = UsdGeom.Cube.Define(stage, '/movingCube')
    cube.CreateSizeAttr(1.0)
    
    # Save the initial setup
    stage.GetRootLayer().Save()
    return stage

def animate_cube(stage: Usd.Stage, velocity: float=0.1, num_frames: int=100, frame_duration: float=1.0) -> None:
    # Setup transform operations for the cube
    xform: UsdGeom.Xformable = UsdGeom.Xformable(stage.GetPrimAtPath('/movingCube'))
    translate_op: UsdGeom.XformOp = xform.AddTranslateOp()
    
    for frame in range(1, num_frames + 1):
        # Calculate translation based on velocity and time
        translation: Gf.Vec3d = velocity * frame * frame_duration
        translate_op.Set(Gf.Vec3f(translation, 0, 0), Usd.TimeCode(frame))
        
        # Explicitly save after each update
        stage.GetRootLayer().Save()
        
        # Print out the frame number to monitor progress
        print(f"Frame {frame}: Cube moved to {translation} meters")
        
        # Wait to simulate real-time updating
        time.sleep(0.1)

def main():
    filename: str = 'movingCube.usda'  # Note the .usda extension for ASCII format
    stage: Usd.Stage = create_usd_file(filename)
    
    # Set up and run the animation loop
    animate_cube(stage, velocity=0.1, num_frames=100, frame_duration=1.0)
    
    print("Animation complete. You can now view the moving cube in usdview.")

if __name__ == "__main__":
    main()