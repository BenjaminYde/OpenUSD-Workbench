#include <iostream>
#include <string>
#include <filesystem>

// Core USD includes
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/sdf/path.h>
#include <pxr/base/gf/vec3d.h>

// USD Geometry includes
#include <pxr/usd/usdGeom/cube.h>
#include <pxr/usd/usdGeom/xformable.h>
#include <pxr/usd/usdGeom/xformOp.h>

PXR_NAMESPACE_USING_DIRECTIVE

void create_hierarchical_cubes(const std::string &filename) {
    // Create stage
    UsdStageRefPtr stage = UsdStage::CreateNew(filename);
    if (!stage) {
        std::cerr << "Error: Could not create stage at " << filename << std::endl;
        return;
    }

    // Create cube 1
    std::string base_path = "/Cube1";
    UsdGeomCube cube1 = UsdGeomCube::Define(stage, SdfPath(base_path));
    cube1.GetSizeAttr().Set(1.0);

    // Create cube 2
    std::string cube2_path = base_path + "/Cube2";
    UsdGeomCube cube2 = UsdGeomCube::Define(stage, SdfPath(cube2_path));
    cube2.GetSizeAttr().Set(0.5);

    UsdGeomXformable xform2(cube2.GetPrim());
    UsdGeomXformOp translate_op2 = xform2.AddTranslateOp();
    translate_op2.Set(GfVec3d(0.0, 0.5f + 0.25f + 0.1f, 0.0));

    // Create cube 3
    std::string cube3_path = cube2_path + "/Cube3";
    UsdGeomCube cube3 = UsdGeomCube::Define(stage, SdfPath(cube3_path));
    cube3.GetSizeAttr().Set(0.25);

    UsdGeomXformable xform3(cube3.GetPrim());
    UsdGeomXformOp translate_op3 = xform3.AddTranslateOp();
    translate_op3.Set(GfVec3d(0.0, 0.25f + 0.1f + 0.125f, 0.0));

    // Save USD file
    stage->GetRootLayer()->Save();
    std::cout << "Successfully saved: " << filename << std::endl;
}

int main(int argc, char *argv[]) {
    std::filesystem::path exe_path = std::filesystem::absolute(argv[0]);
    std::filesystem::path exe_dir = exe_path.parent_path();
    std::filesystem::path output_file = exe_dir / "cubes.usda";

    if (std::filesystem::exists(output_file))
        std::filesystem::remove(output_file);

    create_hierarchical_cubes(output_file.string());
    return 0;
}