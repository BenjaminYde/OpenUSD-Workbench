"""
Generate complete type stubs with docstrings for OpenUSD (pxr)
by introspecting the live C++ extension modules at runtime.

Extracts signatures and docstrings directly from boost.python __doc__ strings,
then applies USD-specific fixes for schema classes, known return types,
implicit conversions, and common boost.python quirks.

Usage:
    python generate_usd_stubs.py [--output-dir ./stubs]

Requirements:
    pip install usd-core
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import re
import sys
import types
from pathlib import Path

# ---------------------------------------------------------------------------
# Boost.python __doc__ parser
# ---------------------------------------------------------------------------

# Matches boost.python signature lines like:
#   Open( (str)filePath [, (InitialLoadSet)load]) -> Stage :
#   __init__( (object)self) -> None :
# Key: use greedy (.*) for params since parens are nested inside
BOOST_SIG_RE = re.compile(
    r"^(\w+)\s*\((.*)\)\s*(?:->\s*(.+?))?\s*:?\s*$", re.MULTILINE
)

# Matches individual boost arg: (Type)name or [(Type)name]
BOOST_ARG_RE = re.compile(
    r"\[?\s*\(([^)]*)\)\s*(\w+)\s*\]?"
)


def parse_boost_doc(doc: str, name: str) -> tuple[list[dict], str]:
    """
    Parse a boost.python __doc__ string into (overloads, docstring).

    Each overload is a dict:
        {"params": [(type, name), ...], "ret": str | None}
    """
    if not doc:
        return [], ""

    lines = doc.strip().split("\n")
    overloads: list[dict] = []
    doc_lines: list[str] = []
    in_sig = True

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if in_sig:
            match = BOOST_SIG_RE.match(line)
            if match and match.group(1) in (name, "__init__"):
                raw_params = match.group(2) or ""
                ret = (match.group(3) or "").strip() or None
                params = BOOST_ARG_RE.findall(raw_params)
                overloads.append({"params": params, "ret": ret})
                i += 1
                continue
            elif not line:
                i += 1
                continue
            else:
                in_sig = False

        if not in_sig:
            doc_lines.append(lines[i])
            i += 1

    docstring = "\n".join(doc_lines).strip()
    docstring = re.sub(
        r"^C\+\+ signature\s*:.*$", "", docstring, flags=re.MULTILINE
    ).strip()

    return overloads, docstring


# ---------------------------------------------------------------------------
# Type mapping & resolution
# ---------------------------------------------------------------------------

# Basic C++/boost type -> Python type
TYPE_MAP: dict[str, str] = {
    "str": "str",
    "string": "str",
    "std::string": "str",
    "TfToken": "str",
    "bool": "bool",
    "int": "int",
    "long": "int",
    "int64_t": "int",
    "uint64_t": "int",
    "size_t": "int",
    "float": "float",
    "double": "float",
    "GfHalf": "float",
    "Half": "float",
    "list": "list",
    "dict": "dict",
    "tuple": "tuple",
    "object": "Any",
    "NoneType": "None",
    "void": "None",
    "VtValue": "Any",
    "VtDictionary": "dict",
}

# Regex-based type cleanups applied in order
TYPE_REGEX: list[tuple[str, str]] = [
    (r"\bpxrInternal_v\d+_\d+__pxrReserved__::", "pxr."),
    (r"\bboost::python::", ""),
    (r"\bstd::", ""),
    (r"\bconst\b\s*", ""),
    (r"\s*[&*]+\s*$", ""),
    (r"\s*[&*]+\s*", " "),
]

# Known implicit conversions: target_type -> set of also-accepted types
IMPLICIT_CONVERSIONS: dict[str, list[str]] = {
    "pxr.Sdf.Path": ["str"],
    "pxr.Sdf.AssetPath": ["str"],
    "pxr.Tf.Token": ["str"],
    "pxr.Sdf.TimeCode": ["float"],
    "pxr.Usd.TimeCode": ["float"],
    "Path": ["str"],
    "AssetPath": ["str"],
    "TimeCode": ["float"],
}

# Known return types for dunder methods (always applied, independent of class)
DUNDER_RETURN_TYPES: dict[str, str] = {
    "__init__": "None",
    "__repr__": "str",
    "__str__": "str",
    "__bool__": "bool",
    "__len__": "int",
    "__hash__": "int",
    "__eq__": "bool",
    "__ne__": "bool",
    "__lt__": "bool",
    "__le__": "bool",
    "__gt__": "bool",
    "__ge__": "bool",
    "__int__": "int",
    "__float__": "float",
    "__contains__": "bool",
    "__iter__": "Iterator",
    "__neg__": "Any",
    "__pos__": "Any",
    "__abs__": "Any",
    "__add__": "Any",
    "__radd__": "Any",
    "__iadd__": "Any",
    "__sub__": "Any",
    "__rsub__": "Any",
    "__isub__": "Any",
    "__mul__": "Any",
    "__rmul__": "Any",
    "__imul__": "Any",
    "__truediv__": "Any",
    "__rtruediv__": "Any",
    "__itruediv__": "Any",
    "__and__": "Any",
    "__or__": "Any",
    "__xor__": "Any",
    "__invert__": "Any",
    "__enter__": "Any",
    "__exit__": "None",
    "__call__": "Any",
    "__getitem__": "Any",
    "__setitem__": "None",
    "__delitem__": "None",
    "__next__": "Any",
}

# Known return types for specific method names (applied to all classes)
KNOWN_RETURN_TYPES: dict[str, str] = {
    "GetSchemaAttributeNames": "list[str]",
    "GetPrim": "pxr.Usd.Prim",
    "GetPath": "pxr.Sdf.Path",
    "GetName": "str",
    "GetTypeName": "str",
    "GetSchemaKind": "pxr.Usd.SchemaKind",
    "GetSchemaType": "pxr.Tf.Type",
    "GetSchemaClassPrimDefinition": "pxr.Usd.PrimDefinition",
    "_GetStaticTfType": "pxr.Tf.Type",
    "IsValid": "bool",
    "IsDefined": "bool",
    "HasAPI": "bool",
    "CanApplyAPI": "bool",
    "ApplyAPI": "bool",
    "RemoveAPI": "bool",
    "GetExtentsHint": "pxr.Vt.Vec3fArray",
    "SetExtentsHint": "bool",
    # Surface faces
    "ComputeSurfaceFaces": "pxr.Vt.IntArray",
    "FindInvertedElements": "pxr.Vt.IntArray",
}

# Schema methods that return the schema class itself
SELF_RETURN_METHODS = {"Define", "Get"}

# Patterns for method names -> return types (applied via regex)
# ORDER MATTERS: more specific patterns first, generic patterns last
RETURN_TYPE_PATTERNS: list[tuple[str, str]] = [
    # --- Primvar (before generic Attr) ---
    (r"^Create\w*Primvar$", "pxr.UsdGeom.Primvar"),
    (r"^Get\w*Primvar$", "pxr.UsdGeom.Primvar"),
    (r"^CreatePrimvar$", "pxr.UsdGeom.Primvar"),
    (r"^GetPrimvar$", "pxr.UsdGeom.Primvar"),
    (r"^GetPrimvars$", "list[pxr.UsdGeom.Primvar]"),
    (r"^GetAuthoredPrimvars$", "list[pxr.UsdGeom.Primvar]"),
    (r"^GetPrimvarsWithValues$", "list[pxr.UsdGeom.Primvar]"),
    (r"^GetPrimvarsWithAuthoredValues$", "list[pxr.UsdGeom.Primvar]"),
    (r"^FindPrimvarWithInheritance$", "pxr.UsdGeom.Primvar"),
    (r"^FindPrimvarsWithInheritance$", "list[pxr.UsdGeom.Primvar]"),
    (r"^FindInheritablePrimvars$", "list[pxr.UsdGeom.Primvar]"),
    (r"^FindIncrementallyInheritablePrimvars$", "list[pxr.UsdGeom.Primvar]"),
    (r"^CreateIndexedPrimvar$", "pxr.UsdGeom.Primvar"),
    (r"^CreateNonIndexedPrimvar$", "pxr.UsdGeom.Primvar"),
    # --- Attribute / Relationship ---
    (r"^Create\w*Attr$", "pxr.Usd.Attribute"),
    (r"^Get\w*Attr$", "pxr.Usd.Attribute"),
    (r"^Create\w*Rel$", "pxr.Usd.Relationship"),
    (r"^Get\w*Rel$", "pxr.Usd.Relationship"),
    # --- XformOp (all Add*Op, Get*Op, MakeMatrixXform) ---
    (r"^Add\w*Op$", "pxr.UsdGeom.XformOp"),
    (r"^Get\w*Op$", "pxr.UsdGeom.XformOp"),
    (r"^MakeMatrixXform$", "pxr.UsdGeom.XformOp"),
    (r"^GetOrderedXformOps$", "list[pxr.UsdGeom.XformOp]"),
    (r"^ClearXformOpOrder$", "None"),
    (r"^GetResetXformStack$", "bool"),
    (r"^TransformMightBeTimeVarying$", "bool"),
    # --- Compute: transforms & bounds ---
    (r"^ComputeLocalToWorldTransform$", "pxr.Gf.Matrix4d"),
    (r"^ComputeParentToWorldTransform$", "pxr.Gf.Matrix4d"),
    (r"^GetLocalToWorldTransform$", "pxr.Gf.Matrix4d"),
    (r"^GetParentToWorldTransform$", "pxr.Gf.Matrix4d"),
    (r"^ComputeRelativeTransform$", "pxr.Gf.Matrix4d"),
    (r"^GetLocalTransformation$", "pxr.Gf.Matrix4d"),
    (r"^GetRotationTransform$", "pxr.Gf.Matrix4d"),
    (r"^ComputeWorldBound$", "pxr.Gf.BBox3d"),
    (r"^ComputeLocalBound$", "pxr.Gf.BBox3d"),
    (r"^ComputeUntransformedBound$", "pxr.Gf.BBox3d"),
    (r"^ComputeRelativeBound$", "pxr.Gf.BBox3d"),
    (r"^ComputeWorldBoundWithOverrides$", "pxr.Gf.BBox3d"),
    (r"^Compute\w*InstanceWorldBound$", "pxr.Gf.BBox3d"),
    (r"^Compute\w*InstanceLocalBound$", "pxr.Gf.BBox3d"),
    (r"^Compute\w*InstanceRelativeBound$", "pxr.Gf.BBox3d"),
    (r"^Compute\w*InstanceUntransformedBound$", "pxr.Gf.BBox3d"),
    (r"^Compute\w*InstanceWorldBounds$", "list[pxr.Gf.BBox3d]"),
    (r"^Compute\w*InstanceLocalBounds$", "list[pxr.Gf.BBox3d]"),
    (r"^Compute\w*InstanceRelativeBounds$", "list[pxr.Gf.BBox3d]"),
    (r"^Compute\w*InstanceUntransformedBounds$", "list[pxr.Gf.BBox3d]"),
    (r"^ComputeInstanceTransformsAtTime$", "pxr.Vt.Matrix4dArray"),
    (r"^ComputeInstanceTransformsAtTimes$", "list[pxr.Vt.Matrix4dArray]"),
    # --- Compute: extent ---
    (r"^ComputeExtent$", "pxr.Vt.Vec3fArray"),
    (r"^ComputeExtentFromPlugins$", "pxr.Vt.Vec3fArray"),
    (r"^ComputeExtentAtTime$", "pxr.Vt.Vec3fArray"),
    (r"^ComputeExtentAtTimes$", "list[pxr.Vt.Vec3fArray]"),
    (r"^ComputeExtentsHint$", "pxr.Vt.Vec3fArray"),
    # --- Compute: purpose / visibility / proxy ---
    (r"^ComputeVisibility$", "str"),
    (r"^ComputeEffectiveVisibility$", "str"),
    (r"^ComputePurpose$", "str"),
    (r"^ComputeModelDrawMode$", "str"),
    (r"^ComputePurposeInfo$", "pxr.UsdGeom.Imageable.PurposeInfo"),
    (r"^ComputeProxyPrim$", "tuple[pxr.Usd.Prim, pxr.Usd.Prim] | None"),
    # --- Compute: points ---
    (r"^ComputePointsAtTime$", "pxr.Vt.Vec3fArray"),
    (r"^ComputePointsAtTimes$", "list[pxr.Vt.Vec3fArray]"),
    (r"^ComputeFlattened$", "Any"),
    # --- Compute: interpolation / data sizes ---
    (r"^ComputeInterpolationForSize$", "str"),
    (r"^ComputeUniformDataSize$", "int"),
    (r"^ComputeVaryingDataSize$", "int"),
    (r"^ComputeVertexDataSize$", "int"),
    (r"^ComputeSegmentCounts$", "pxr.Vt.IntArray"),
    # --- Compute: misc ---
    (r"^ComputeMaskAtTime$", "list[bool]"),
    (r"^Compute\w*Scale$", "float"),
    (r"^ComputeNonlinearSampleCount$", "int"),
    (r"^ComputeMotionBlurScale$", "float"),
    (r"^ComputeVelocityScale$", "float"),
    (r"^ComputeLinearExposureScale$", "float"),
    # --- Time samples ---
    (r"^GetTimeSamples$", "list[float]"),
    (r"^GetTimeSamplesInInterval$", "list[float]"),
    (r"^GetNumTimeSamples$", "int"),
    (r"^GetTime$", "pxr.Usd.TimeCode"),
    (r"^GetBaseTime$", "pxr.Usd.TimeCode"),
    # --- Interpolation / string token getters ---
    (r"^Get\w*Interpolation$", "str"),
    (r"^GetBaseName$", "str"),
    (r"^GetNamespace$", "str"),
    (r"^GetOpName$", "str"),
    (r"^GetIdentifier$", "str"),
    (r"^GetPrimvarName$", "str"),
    (r"^SplitName$", "list[str]"),
    (r"^GetDeclarationInfo$", "tuple"),
    # --- Name / token lists ---
    (r"^GetOrdered\w+Names$", "list[str]"),
    (r"^GetOrderedPurposeTokens$", "list[str]"),
    (r"^GetAll\w+FamilyNames$", "list[str]"),
    # --- Schema queries ---
    (r"^Apply$", "pxr.Usd.Prim"),
    (r"^CanApply$", "bool"),
    # --- Subset methods ---
    (r"^CreateGeomSubset$", "pxr.UsdGeom.Subset"),
    (r"^CreateUniqueGeomSubset$", "pxr.UsdGeom.Subset"),
    (r"^GetAllGeomSubsets$", "list[pxr.UsdGeom.Subset]"),
    (r"^GetGeomSubsets$", "list[pxr.UsdGeom.Subset]"),
    (r"^GetFamilyType$", "str"),
    (r"^GetUnassignedIndices$", "pxr.Vt.IntArray"),
    (r"^ValidateFamily$", "bool"),
    (r"^ValidateSubsets$", "bool"),
    (r"^ValidateTopology$", "bool"),
    # --- Constraint targets ---
    (r"^CreateConstraintTarget$", "pxr.UsdGeom.ConstraintTarget"),
    (r"^GetConstraintTarget$", "pxr.UsdGeom.ConstraintTarget"),
    (r"^GetConstraintTargets$", "list[pxr.UsdGeom.ConstraintTarget]"),
    (r"^ComputeInWorldSpace$", "pxr.Gf.Matrix4d"),
    # --- Camera ---
    (r"^GetCamera$", "pxr.Gf.Camera"),
    (r"^SetFromCamera$", "None"),
    # --- XformCommonAPI ---
    (r"^GetXformVectors$", "tuple"),
    (r"^GetXformVectorsByAccumulation$", "tuple"),
    (r"^CreateXformOps$", "tuple"),
    (r"^ConvertOpTypeToRotationOrder$", "int"),
    (r"^ConvertRotationOrderToOpType$", "int"),
    (r"^CanConvertOpTypeToRotationOrder$", "bool"),
    # --- XformOp ---
    (r"^GetOpTransform$", "pxr.Gf.Matrix4d"),
    (r"^GetOpType$", "int"),
    (r"^GetOpTypeEnum$", "int"),
    (r"^GetOpTypeToken$", "str"),
    (r"^GetPrecision$", "int"),
    (r"^IsInverseOp$", "bool"),
    (r"^MightBeTimeVarying$", "bool"),
    (r"^ValueMightBeTimeVarying$", "bool"),
    # --- PointInstancer: activate / deactivate / vis / invis ---
    (r"^ActivateId$", "bool"),
    (r"^ActivateIds$", "bool"),
    (r"^ActivateAllIds$", "bool"),
    (r"^DeactivateId$", "bool"),
    (r"^DeactivateIds$", "bool"),
    (r"^InvisId$", "bool"),
    (r"^InvisIds$", "bool"),
    (r"^VisId$", "bool"),
    (r"^VisIds$", "bool"),
    (r"^VisAllIds$", "bool"),
    (r"^GetInstanceCount$", "int"),
    # --- Boolean queries (generic, keep near bottom) ---
    (r"^Has\w+$", "bool"),
    (r"^Is\w+$", "bool"),
    (r"^Can\w+$", "bool"),
    (r"^NameContainsNamespaces$", "bool"),
    # --- Setters (generic, keep near bottom) ---
    (r"^Set\w+$", "bool"),
    # --- Clear / Remove / Block / Make (generic) ---
    (r"^Clear\w*$", "None"),
    (r"^Remove\w*$", "None"),
    (r"^Block\w*$", "None"),
    (r"^MakeInvisible$", "None"),
    (r"^MakeVisible$", "None"),
    (r"^Swap$", "None"),
    # --- Count methods ---
    (r"^Get\w*Count$", "int"),
    (r"^GetElementSize$", "int"),
    (r"^GetUnauthoredValuesIndex$", "int"),
]

# Module-level functions with known return types
MODULE_FUNC_RETURN_TYPES: dict[str, str] = {
    "pxr.UsdGeom.GetFallbackUpAxis": "str",
    "pxr.UsdGeom.GetStageUpAxis": "str",
    "pxr.UsdGeom.SetStageUpAxis": "bool",
    "pxr.UsdGeom.GetStageMetersPerUnit": "float",
    "pxr.UsdGeom.SetStageMetersPerUnit": "bool",
    "pxr.UsdGeom.StageHasAuthoredMetersPerUnit": "bool",
    "pxr.UsdGeom.LinearUnitsAre": "bool",
    "pxr.Usd.Stage.Open": "pxr.Usd.Stage",
    "pxr.Usd.Stage.OpenLayer": "pxr.Usd.Stage",
    "pxr.Usd.Stage.CreateNew": "pxr.Usd.Stage",
    "pxr.Usd.Stage.CreateInMemory": "pxr.Usd.Stage",
    "pxr.Sdf.Layer.FindOrOpen": "pxr.Sdf.Layer",
    "pxr.Sdf.Layer.CreateNew": "pxr.Sdf.Layer",
    "pxr.Sdf.Layer.CreateAnonymous": "pxr.Sdf.Layer",
    "pxr.Sdf.Layer.Find": "pxr.Sdf.Layer",
    "pxr.Sdf.Layer.OpenAsAnonymous": "pxr.Sdf.Layer",
    "pxr.Sdf.Layer.GetExternalReferences": "list[str]",
    "pxr.Sdf.Layer.GetCompositionAssetDependencies": "list[str]",
    "pxr.Sdf.PrimSpec.nameRoot": "pxr.Sdf.PrimSpec",
    "pxr.Usd.Prim.GetChildren": "list[pxr.Usd.Prim]",
    "pxr.Usd.Prim.GetAllChildren": "list[pxr.Usd.Prim]",
    "pxr.Usd.Prim.GetFilteredChildren": "list[pxr.Usd.Prim]",
    "pxr.Usd.Prim.GetAttributes": "list[pxr.Usd.Attribute]",
    "pxr.Usd.Prim.GetRelationships": "list[pxr.Usd.Relationship]",
    "pxr.Usd.Prim.GetProperties": "list[pxr.Usd.Property]",
    "pxr.Usd.Prim.GetAttribute": "pxr.Usd.Attribute",
    "pxr.Usd.Prim.GetRelationship": "pxr.Usd.Relationship",
    "pxr.Usd.Prim.GetProperty": "pxr.Usd.Property",
    "pxr.Usd.Prim.CreateAttribute": "pxr.Usd.Attribute",
    "pxr.Usd.Prim.CreateRelationship": "pxr.Usd.Relationship",
    "pxr.Usd.Prim.GetParent": "pxr.Usd.Prim",
    "pxr.Usd.Prim.GetPrimDefinition": "pxr.Usd.PrimDefinition",
    "pxr.Usd.Prim.GetStage": "pxr.Usd.Stage",
    "pxr.Usd.Prim.GetTypeName": "str",
    "pxr.Usd.Prim.GetName": "str",
    "pxr.Usd.Prim.GetPath": "pxr.Sdf.Path",
    "pxr.Usd.Attribute.Get": "Any",
    "pxr.Usd.Attribute.Set": "bool",
    "pxr.Usd.Stage.GetPrimAtPath": "pxr.Usd.Prim",
    "pxr.Usd.Stage.DefinePrim": "pxr.Usd.Prim",
    "pxr.Usd.Stage.OverridePrim": "pxr.Usd.Prim",
    "pxr.Usd.Stage.CreateClassPrim": "pxr.Usd.Prim",
    "pxr.Usd.Stage.GetDefaultPrim": "pxr.Usd.Prim",
    "pxr.Usd.Stage.GetPseudoRoot": "pxr.Usd.Prim",
    "pxr.Usd.Stage.GetRootLayer": "pxr.Sdf.Layer",
    "pxr.Usd.Stage.GetSessionLayer": "pxr.Sdf.Layer",
    "pxr.Usd.Stage.Traverse": "list[pxr.Usd.Prim]",
    "pxr.Usd.Stage.TraverseAll": "list[pxr.Usd.Prim]",
    "pxr.Usd.Stage.Flatten": "pxr.Sdf.Layer",
    "pxr.Usd.Stage.Export": "bool",
    "pxr.Usd.Stage.Save": "None",
    "pxr.Usd.Stage.GetStartTimeCode": "float",
    "pxr.Usd.Stage.GetEndTimeCode": "float",
    "pxr.Usd.Stage.HasDefaultPrim": "bool",
    "pxr.Usd.Stage.RemovePrim": "bool",
    "pxr.UsdGeom.Xformable.GetOrderedXformOps": "list[pxr.UsdGeom.XformOp]",
    "pxr.UsdGeom.Xformable.AddXformOp": "pxr.UsdGeom.XformOp",
    "pxr.UsdGeom.Xformable.AddTranslateOp": "pxr.UsdGeom.XformOp",
    "pxr.UsdGeom.Xformable.AddRotateXYZOp": "pxr.UsdGeom.XformOp",
    "pxr.UsdGeom.Xformable.AddScaleOp": "pxr.UsdGeom.XformOp",
    "pxr.UsdGeom.Xformable.MakeMatrixXform": "pxr.UsdGeom.XformOp",
    "pxr.UsdGeom.Imageable.ComputeLocalToWorldTransform": "pxr.Gf.Matrix4d",
    "pxr.UsdGeom.Imageable.ComputeWorldBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputeWorldBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.XformCache.GetLocalToWorldTransform": "pxr.Gf.Matrix4d",
    "pxr.UsdGeom.BBoxCache.ComputeLocalBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputeRelativeBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputeUntransformedBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputeWorldBoundWithOverrides": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputePointInstanceWorldBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputePointInstanceLocalBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputePointInstanceRelativeBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.ComputePointInstanceUntransformedBound": "pxr.Gf.BBox3d",
    "pxr.UsdGeom.BBoxCache.GetTime": "pxr.Usd.TimeCode",
    "pxr.UsdGeom.BBoxCache.GetBaseTime": "pxr.Usd.TimeCode",
    "pxr.UsdGeom.BBoxCache.GetIncludedPurposes": "list[str]",
    "pxr.UsdGeom.BBoxCache.GetUseExtentsHint": "bool",
    "pxr.UsdGeom.BBoxCache.HasBaseTime": "bool",
    "pxr.UsdGeom.BBoxCache.SetBaseTime": "None",
    "pxr.UsdGeom.BBoxCache.SetTime": "None",
    "pxr.UsdGeom.BBoxCache.SetIncludedPurposes": "None",
    "pxr.UsdGeom.BBoxCache.Clear": "None",
    "pxr.UsdGeom.BBoxCache.ClearBaseTime": "None",
    "pxr.UsdGeom.XformCache.GetLocalTransformation": "pxr.Gf.Matrix4d",
    "pxr.UsdGeom.XformCache.GetParentToWorldTransform": "pxr.Gf.Matrix4d",
    "pxr.UsdGeom.XformCache.ComputeRelativeTransform": "pxr.Gf.Matrix4d",
    "pxr.UsdGeom.XformCache.GetTime": "pxr.Usd.TimeCode",
    "pxr.UsdGeom.XformCache.SetTime": "None",
    "pxr.UsdGeom.XformCache.Clear": "None",
    "pxr.UsdGeom.XformCache.Swap": "None",
    "pxr.UsdShade.Material.CreateSurfaceOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Material.CreateDisplacementOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Material.CreateVolumeOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Material.GetSurfaceOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Shader.CreateInput": "pxr.UsdShade.Input",
    "pxr.UsdShade.Shader.CreateOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Shader.GetInput": "pxr.UsdShade.Input",
    "pxr.UsdShade.Shader.GetOutput": "pxr.UsdShade.Output",
    "pxr.UsdShade.Shader.GetInputs": "list[pxr.UsdShade.Input]",
    "pxr.UsdShade.Shader.GetOutputs": "list[pxr.UsdShade.Output]",
}


def _build_schema_class_set() -> set[str]:
    """Discover all USD schema classes by checking for Define or GetPrim."""
    import pxr

    schema_classes: set[str] = set()
    for mod_name in pxr.__all__:
        try:
            mod = importlib.import_module(f"pxr.{mod_name}")
        except ImportError:
            continue
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if hasattr(obj, "GetPrim") or hasattr(obj, "Define"):
                schema_classes.add(f"pxr.{mod_name}.{name}")
    return schema_classes


# Lazily populated
_schema_classes: set[str] | None = None


def get_schema_classes() -> set[str]:
    global _schema_classes
    if _schema_classes is None:
        _schema_classes = _build_schema_class_set()
    return _schema_classes


def sanitize_type(type_str: str) -> str:
    """Clean up C++/boost type names into Python-friendly type hints."""
    if not type_str:
        return "Any"

    s = type_str.strip()

    if s in TYPE_MAP:
        return TYPE_MAP[s]

    for pattern, repl in TYPE_REGEX:
        s = re.sub(pattern, repl, s)

    s = s.strip()

    if s in TYPE_MAP:
        return TYPE_MAP[s]

    return s if s else "Any"


def resolve_return_type(
    name: str,
    boost_ret: str | None,
    full_class_path: str | None,
    full_func_path: str | None,
) -> str:
    """Determine the best return type for a method."""

    # 0. Dunder methods always have known types
    if name in DUNDER_RETURN_TYPES:
        return DUNDER_RETURN_TYPES[name]

    # 1. Explicit full-path overrides (highest priority)
    if full_func_path and full_func_path in MODULE_FUNC_RETURN_TYPES:
        return MODULE_FUNC_RETURN_TYPES[full_func_path]

    # 2. Schema self-returning methods
    if full_class_path and full_class_path in get_schema_classes():
        class_short = full_class_path.split(".")[-1]

        if name in SELF_RETURN_METHODS:
            return class_short

    # 3. Known method names (apply to all classes)
    if name in KNOWN_RETURN_TYPES:
        return KNOWN_RETURN_TYPES[name]

    # 4. Pattern matching (apply to all classes)
    for pattern, ret_type in RETURN_TYPE_PATTERNS:
        if re.match(pattern, name):
            return ret_type

    # 5. Use boost's return type if it's something concrete (not "object")
    if boost_ret:
        sanitized = sanitize_type(boost_ret)
        # "object" in boost means "we don't know" -> becomes Any
        # But specific types from boost are trustworthy
        if sanitized not in ("Any", "object"):
            return sanitized
        # Check if the raw boost type looks like a pxr class name
        if boost_ret and boost_ret not in ("object", "None", "list", "dict", "tuple"):
            # Might be a class name like "Stage", "Layer", etc.
            clean = boost_ret.strip()
            if clean and clean[0].isupper() and clean.isidentifier():
                return clean

    if name == "__init__":
        return "None"

    return "Any"


def resolve_arg_type(type_str: str) -> str:
    """Resolve an argument type, adding implicit conversion unions."""
    base = sanitize_type(type_str)

    # Add implicit conversions
    if base in IMPLICIT_CONVERSIONS:
        alt_types = IMPLICIT_CONVERSIONS[base]
        return " | ".join([base] + alt_types)

    # Check for full-path types
    for target, alts in IMPLICIT_CONVERSIONS.items():
        short = target.split(".")[-1]
        if base == short:
            return " | ".join([base] + alts)

    return base


# ---------------------------------------------------------------------------
# Stub generation
# ---------------------------------------------------------------------------

def format_docstring(doc: str, indent: str) -> str:
    if not doc:
        return ""

    lines = doc.split("\n")

    if len(lines) == 1 and len(lines[0]) < 80:
        return f'{indent}"""{lines[0]}"""\n'

    result = f'{indent}"""\n'
    for line in lines:
        if line.strip():
            result += f"{indent}{line}\n"
        else:
            result += "\n"
    result += f'{indent}"""\n'
    return result


def is_boost_method(obj) -> bool:
    type_name = type(obj).__name__
    return type_name in (
        "Boost.Python.function",
        "method_descriptor",
        "builtin_function_or_method",
        "method-wrapper",
        "instancemethod",
        "getset_descriptor",
        "Boost.Python.StaticProperty",
    )


def format_sig(
    params: list[tuple[str, str]],
    is_method: bool,
    is_static: bool,
) -> str:
    """Build a (params) string from parsed boost args."""
    parts: list[str] = []

    skip_self = False
    for i, (ptype, pname) in enumerate(params):
        # Skip the implicit self arg boost sometimes adds
        if i == 0 and is_method and not is_static:
            if pname in ("self", "arg1") and ptype in ("object", ""):
                skip_self = True
                continue
            elif ptype == "object" and pname.startswith("arg"):
                skip_self = True
                continue

        resolved = resolve_arg_type(ptype)
        parts.append(f"{pname}: {resolved}")

    if is_method and not is_static:
        return "(self, {})".format(", ".join(parts)) if parts else "(self)"
    else:
        return "({})".format(", ".join(parts))


def generate_function_stub(
    name: str,
    obj,
    indent: str,
    is_method: bool = False,
    is_static: bool = False,
    full_class_path: str | None = None,
    module_name: str | None = None,
) -> str:
    """Generate stub lines for a function or method."""
    doc = getattr(obj, "__doc__", "") or ""
    overloads, docstring = parse_boost_doc(doc, name)

    full_func_path = None
    if full_class_path:
        full_func_path = f"{full_class_path}.{name}"
    elif module_name:
        full_func_path = f"{module_name}.{name}"

    result = ""

    if not overloads:
        # Fallback: generic signature
        ret = resolve_return_type(name, None, full_class_path, full_func_path)
        if is_static:
            result += f"{indent}@staticmethod\n"
            result += f"{indent}def {name}(*args, **kwargs) -> {ret}:\n"
        elif is_method:
            result += f"{indent}def {name}(self, *args, **kwargs) -> {ret}:\n"
        else:
            result += f"{indent}def {name}(*args, **kwargs) -> {ret}:\n"

        if docstring:
            result += format_docstring(docstring, indent + "    ")
        else:
            result += f"{indent}    ...\n"
        return result

    use_overload = len(overloads) > 1

    for i, ov in enumerate(overloads):
        if use_overload:
            result += f"{indent}@overload\n"
        if is_static:
            result += f"{indent}@staticmethod\n"

        params = ov["params"]
        ret = resolve_return_type(name, ov["ret"], full_class_path, full_func_path)
        sig = format_sig(params, is_method, is_static)

        result += f"{indent}def {name}{sig} -> {ret}:\n"

        if docstring and i == 0:
            result += format_docstring(docstring, indent + "    ")
        else:
            result += f"{indent}    ...\n"

    return result


def generate_property_stub(
    name: str,
    obj,
    indent: str,
    full_class_path: str | None = None,
) -> str:
    result = f"{indent}@property\n"

    doc = getattr(obj, "__doc__", "") or ""

    # Known property types
    KNOWN_PROPERTY_TYPES = {
        "name": "str",
        "fullName": "str",
        "displayName": "str",
        "value": "int",
        "isInheritable": "bool",
        "purpose": "str",
        "expired": "bool",
        "typeName": "str",
        "interpolation": "str",
        "elementSize": "int",
    }

    prop_type = KNOWN_PROPERTY_TYPES.get(name, "Any")

    # Try to infer from getter doc if not known
    if prop_type == "Any" and doc:
        overloads, _ = parse_boost_doc(doc, name)
        if overloads and overloads[0]["ret"]:
            prop_type = sanitize_type(overloads[0]["ret"])

    result += f"{indent}def {name}(self) -> {prop_type}:\n"

    if doc.strip():
        result += format_docstring(doc.strip(), indent + "    ")
    else:
        result += f"{indent}    ...\n"

    return result


# Dunder methods to include in stubs
DUNDER_ALLOWLIST = frozenset({
    "__init__", "__repr__", "__str__", "__eq__", "__ne__",
    "__lt__", "__le__", "__gt__", "__ge__", "__hash__",
    "__len__", "__iter__", "__next__", "__getitem__",
    "__setitem__", "__delitem__", "__contains__",
    "__add__", "__radd__", "__iadd__",
    "__sub__", "__rsub__", "__isub__",
    "__mul__", "__rmul__", "__imul__",
    "__truediv__", "__rtruediv__", "__itruediv__",
    "__floordiv__", "__mod__", "__pow__",
    "__neg__", "__pos__", "__abs__", "__invert__",
    "__and__", "__or__", "__xor__",
    "__bool__", "__int__", "__float__",
    "__enter__", "__exit__", "__call__",
})


def generate_class_stub(
    name: str,
    cls,
    indent: str,
    module_name: str | None = None,
) -> str:
    full_class_path = f"{module_name}.{name}" if module_name else name

    # Base classes
    bases = []
    for base in getattr(cls, "__bases__", ()):
        if base is object:
            continue
        bname = base.__name__
        if base.__module__.startswith("pxr."):
            bname = f"{base.__module__}.{base.__name__}"
        bases.append(bname)

    bases_str = f"({', '.join(bases)})" if bases else ""
    result = f"{indent}class {name}{bases_str}:\n"

    inner = indent + "    "

    # Class docstring
    class_doc = getattr(cls, "__doc__", "") or ""
    if class_doc.strip():
        clean = class_doc.strip()
        if not BOOST_SIG_RE.match(clean.split("\n")[0]):
            result += format_docstring(clean, inner)
        else:
            _, doc_part = parse_boost_doc(clean, name)
            if doc_part:
                result += format_docstring(doc_part, inner)

    # Collect members
    members: dict[str, object] = {}
    try:
        members = {
            k: v
            for k, v in inspect.getmembers(cls)
            if not k.startswith("_") or k in DUNDER_ALLOWLIST
        }
    except Exception:
        pass

    has_body = False

    # __init__
    if "__init__" in members:
        result += generate_function_stub(
            "__init__", members["__init__"], inner,
            is_method=True, full_class_path=full_class_path, module_name=module_name,
        )
        has_body = True

    # Properties
    for mname, mobj in sorted(members.items()):
        if mname == "__init__":
            continue
        if isinstance(mobj, property) or type(mobj).__name__ in (
            "getset_descriptor", "Boost.Python.StaticProperty"
        ):
            result += generate_property_stub(mname, mobj, inner, full_class_path)
            has_body = True

    # Methods
    for mname, mobj in sorted(members.items()):
        if mname == "__init__":
            continue
        if isinstance(mobj, property) or type(mobj).__name__ in (
            "getset_descriptor", "Boost.Python.StaticProperty"
        ):
            continue
        if callable(mobj) or is_boost_method(mobj):
            is_static = isinstance(
                inspect.getattr_static(cls, mname, None),
                staticmethod,
            )
            result += generate_function_stub(
                mname, mobj, inner,
                is_method=True, is_static=is_static,
                full_class_path=full_class_path, module_name=module_name,
            )
            has_body = True

    # Inner classes / enums
    for mname, mobj in sorted(members.items()):
        if isinstance(mobj, type) and not mname.startswith("_"):
            result += generate_class_stub(
                mname, mobj, inner,
                module_name=full_class_path,
            )
            has_body = True

    if not has_body:
        result += f"{inner}...\n"

    return result


def localize_type(type_str: str, module_name: str, imports: set[str]) -> str:
    """Convert fully-qualified type refs to local or imported names.

    Within pxr.Usd stubs, 'pxr.Usd.Stage' becomes 'Stage'.
    Cross-module refs like 'pxr.Sdf.Path' get an import added and become 'Sdf.Path'.
    """
    if not type_str:
        return type_str

    def _replace_one(match: re.Match) -> str:
        full = match.group(0)
        # e.g. full = "pxr.Usd.Stage" or "pxr.Sdf.Path"
        parts = full.split(".")
        if len(parts) < 3 or parts[0] != "pxr":
            return full
        ref_module = f"pxr.{parts[1]}"  # e.g. "pxr.Sdf"
        ref_type = ".".join(parts[2:])   # e.g. "Path" or "Imageable.PurposeInfo"

        if ref_module == module_name:
            # Same module: use short name
            return ref_type
        else:
            # Cross-module: import and use Module.Type
            imports.add(f"from pxr import {parts[1]}")
            return f"{parts[1]}.{ref_type}"

    # Match pxr.Module.Type patterns (including nested like pxr.UsdGeom.Imageable.PurposeInfo)
    return re.sub(r"pxr\.\w+(?:\.\w+)+", _replace_one, type_str)


def generate_module_stub(module_name: str) -> str | None:
    try:
        mod = importlib.import_module(module_name)
    except ImportError as e:
        print(f"  Could not import {module_name}: {e}")
        return None

    # Collect cross-module imports during generation
    cross_imports: set[str] = set()

    lines = [
        "from __future__ import annotations",
        "from typing import Any, ClassVar, Iterator, overload",
        "",
    ]

    members: dict[str, object] = {}
    try:
        if hasattr(mod, "__all__"):
            for mname in mod.__all__:
                try:
                    members[mname] = getattr(mod, mname)
                except AttributeError:
                    pass
        else:
            members = {
                k: v for k, v in inspect.getmembers(mod)
                if not k.startswith("_")
            }
    except Exception as e:
        print(f"  Could not inspect {module_name}: {e}")
        return None

    classes: dict[str, type] = {}
    functions: dict[str, object] = {}
    constants: dict[str, object] = {}

    for mname, obj in sorted(members.items()):
        if isinstance(obj, type):
            classes[mname] = obj
        elif callable(obj) or is_boost_method(obj):
            functions[mname] = obj
        elif isinstance(obj, types.ModuleType):
            continue
        else:
            constants[mname] = obj

    # Constants
    for mname, obj in sorted(constants.items()):
        if isinstance(obj, str):
            lines.append(f"{mname}: str")
        elif isinstance(obj, bool):
            lines.append(f"{mname}: bool")
        elif isinstance(obj, int):
            lines.append(f"{mname}: int")
        elif isinstance(obj, float):
            lines.append(f"{mname}: float")
        else:
            lines.append(f"{mname}: {type(obj).__name__}")
    if constants:
        lines.append("")

    # Functions
    for mname, obj in sorted(functions.items()):
        lines.append(generate_function_stub(
            mname, obj, "", module_name=module_name,
        ))
        lines.append("")

    # Classes
    for mname, obj in sorted(classes.items()):
        lines.append(generate_class_stub(
            mname, obj, "", module_name=module_name,
        ))
        lines.append("")

    raw = "\n".join(lines)

    # Post-process: localize all pxr.X.Y type references
    cross_imports: set[str] = set()
    localized = localize_type(raw, module_name, cross_imports)

    # Insert cross-module imports after the typing import line
    if cross_imports:
        import_block = "\n".join(sorted(cross_imports))
        localized = localized.replace(
            "from typing import Any, ClassVar, Iterator, overload\n",
            f"from typing import Any, ClassVar, Iterator, overload\n{import_block}\n",
        )

    return localized


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate USD pxr type stubs with docstrings via runtime introspection"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("./stubs"),
        help="Directory to write stubs to (default: ./stubs)",
    )
    args = parser.parse_args()

    try:
        import pxr
    except ImportError:
        print("Error: 'pxr' is not installed.")
        print("  uv pip install usd-core")
        sys.exit(1)

    output_dir = args.output_dir
    pxr_dir = output_dir / "pxr"
    pxr_dir.mkdir(parents=True, exist_ok=True)

    # Pre-populate schema class set
    print("Discovering schema classes...")
    schemas = get_schema_classes()
    print(f"Found {len(schemas)} schema classes\n")

    submodules = []
    for mname in pxr.__all__:
        fqn = f"pxr.{mname}"
        try:
            importlib.import_module(fqn)
            submodules.append((mname, fqn))
        except ImportError as e:
            print(f"  Skipping {fqn}: {e}")

    print(f"Found {len(submodules)} pxr submodules\n")

    # Top-level pxr/__init__.pyi
    init_lines = ["from __future__ import annotations\n"]
    for mname, _ in submodules:
        init_lines.append(f"from pxr import {mname} as {mname}")
    init_lines.append("")
    all_list = ", ".join(f"'{mname}'" for mname, _ in submodules)
    init_lines.append(f"__all__ = [{all_list}]")
    (pxr_dir / "__init__.pyi").write_text("\n".join(init_lines))

    succeeded = 0
    failed = 0
    total_classes = 0
    total_functions = 0
    total_any_returns = 0
    total_typed_returns = 0

    for mname, fqn in submodules:
        print(f"Generating stubs for {fqn}...")
        stub_content = generate_module_stub(fqn)

        if stub_content is None:
            failed += 1
            continue

        mod_dir = pxr_dir / mname
        mod_dir.mkdir(parents=True, exist_ok=True)
        (mod_dir / "__init__.pyi").write_text(stub_content)

        n_classes = stub_content.count("\nclass ")
        n_funcs = stub_content.count("\ndef ")
        n_any = stub_content.count("-> Any:")
        n_typed = n_funcs - n_any
        total_classes += n_classes
        total_functions += n_funcs
        total_any_returns += n_any
        total_typed_returns += n_typed
        print(f"  -> {n_classes} classes, {n_funcs} functions ({n_any} -> Any, {n_typed} typed)")
        succeeded += 1

    pct = (total_typed_returns / total_functions * 100) if total_functions else 0
    print(f"\n{'='*60}")
    print(f"Modules:    {succeeded} succeeded, {failed} failed")
    print(f"Total:      {total_classes} classes, {total_functions} functions/methods")
    print(f"Typed:      {total_typed_returns}/{total_functions} ({pct:.1f}%) have return types")
    print(f"Remaining:  {total_any_returns} still -> Any")
    print(f"Output:     {output_dir.resolve()}")
    print(f"\npyproject.toml (mypy):")
    print(f'  [tool.mypy]')
    print(f'  mypy_path = "{output_dir}"')
    print(f"\npyproject.toml (pyright/pylance):")
    print(f'  [tool.pyright]')
    print(f'  stubPath = "{output_dir}"')


if __name__ == "__main__":
    main()