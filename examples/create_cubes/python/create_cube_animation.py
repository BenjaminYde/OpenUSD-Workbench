import pxr.Usd
import pxr.UsdGeom
import pxr.Gf
import time

def create_usd_file(filename):
    # Create a new stage with ASCII format
    stage = pxr.Usd.Stage.CreateNew(filename)
    
    # Define a Cube primitive at the root layer
    cube = pxr.UsdGeom.Cube.Define(stage, '/movingCube')
    cube.CreateSizeAttr(1.0)
    
    # Save the initial setup
    stage.GetRootLayer().Save()
    return stage

def animate_cube(stage, velocity=0.1, num_frames=100, frame_duration=1.0):
    # Setup transform operations for the cube
    xform = pxr.UsdGeom.Xformable(stage.GetPrimAtPath('/movingCube'))
    translate_op = xform.AddTranslateOp()
    
    for frame in range(1, num_frames + 1):
        # Calculate translation based on velocity and time
        translation = velocity * frame * frame_duration
        translate_op.Set(pxr.Gf.Vec3f(translation, 0, 0), pxr.Usd.TimeCode(frame))
        
        # Explicitly save after each update
        stage.GetRootLayer().Save()
        
        # Print out the frame number to monitor progress
        print(f"Frame {frame}: Cube moved to {translation} meters")
        
        # Wait to simulate real-time updating
        time.sleep(0.1)

def main():
    filename = 'movingCube.usda'  # Note the .usda extension for ASCII format
    stage = create_usd_file(filename)
    
    # Set up and run the animation loop
    animate_cube(stage, velocity=0.1, num_frames=100, frame_duration=1.0)
    
    print("Animation complete. You can now view the moving cube in usdview.")

if __name__ == "__main__":
    main()
