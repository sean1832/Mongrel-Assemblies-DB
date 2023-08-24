using System;
using System.Collections;
using System.Collections.Generic;

using Rhino;
using Rhino.Geometry;

using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;

using System.Linq;
using System.IO;


/// <summary>
/// This class will be instantiated on demand by the Script component.
/// </summary>
public abstract class Script_Instance_5a983 : GH_ScriptInstance
{
  #region Utility functions
  /// <summary>Print a String to the [Out] Parameter of the Script component.</summary>
  /// <param name="text">String to print.</param>
  private void Print(string text) { /* Implementation hidden. */ }
  /// <summary>Print a formatted String to the [Out] Parameter of the Script component.</summary>
  /// <param name="format">String format.</param>
  /// <param name="args">Formatting parameters.</param>
  private void Print(string format, params object[] args) { /* Implementation hidden. */ }
  /// <summary>Print useful information about an object instance to the [Out] Parameter of the Script component. </summary>
  /// <param name="obj">Object instance to parse.</param>
  private void Reflect(object obj) { /* Implementation hidden. */ }
  /// <summary>Print the signatures of all the overloads of a specific method to the [Out] Parameter of the Script component. </summary>
  /// <param name="obj">Object instance to parse.</param>
  private void Reflect(object obj, string method_name) { /* Implementation hidden. */ }
  #endregion

  #region Members
  /// <summary>Gets the current Rhino document.</summary>
  private readonly RhinoDoc RhinoDocument;
  /// <summary>Gets the Grasshopper document that owns this script.</summary>
  private readonly GH_Document GrasshopperDocument;
  /// <summary>Gets the Grasshopper script component that owns this script.</summary>
  private readonly IGH_Component Component;
  /// <summary>
  /// Gets the current iteration count. The first call to RunScript() is associated with Iteration==0.
  /// Any subsequent call within the same solution will increment the Iteration count.
  /// </summary>
  private readonly int Iteration;
  #endregion
  /// <summary>
  /// This procedure contains the user code. Input parameters are provided as regular arguments,
  /// Output parameters as ref arguments. You don't have to assign output parameters,
  /// they will have a default value.
  /// </summary>
  #region Runscript
  private void RunScript(List<string> localPaths, bool import, ref object out_geos)
  {

    if (import)
    {
      geometries.Clear();
      msg = "";
      int pathIndex = 0;
      foreach (var path in localPaths)
      {
        GH_Path ghPath = new GH_Path(pathIndex);
        if (path.EndsWith(".obj"))
        {
          var _geometries = ImportMesh(path);
          var combinedMesh = new Mesh();
          foreach (var geo in _geometries)
          {
            combinedMesh.Append(geo as Mesh);
          }
          geometries.Add(combinedMesh, ghPath);
        }
        else if (path.EndsWith(".3dm"))
        {
          var _geometries = Import3DM(path);
          if (_geometries.Count == 0)
          {
            Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "No geometry found in the file\n" + path);
            return;
          }
          else
          {
            foreach (var geo in _geometries)
            {
              geometries.Add(geo, ghPath);
            }
          }
        }
        else
        {
          msg = "File format not supported!";
          Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "File format not supported yet");
        }
        pathIndex++;
      }
      // After the import is done, turn off the import toggle
      ChangeInputToggle("import", false);
      msg = "Imported " + geometries.BranchCount.ToString() + " files";
    }
    out_geos = geometries;
    Component.Message = msg;
  }
  #endregion
  #region Additional
  //private List<GeometryBase> geometries = new List<GeometryBase>();
  private DataTree<GeometryBase> geometries = new DataTree<GeometryBase>();

  private string msg = "";

  private List<GeometryBase> ImportMesh(string path)
  {
    RhinoDoc.ActiveDoc.Objects.UnselectAll();
    string cmd = "-_Import \"" + path + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_SelAll _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_Mesh _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_SelMesh _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_Join _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    // get the selected objects
    var selectObjs = RhinoDoc.ActiveDoc.Objects.GetSelectedObjects(false, false).ToList();
    List<GeometryBase> geos = new List<GeometryBase>();

    // get the meshes
    foreach (var selectObj in selectObjs)
    {
      GeometryBase geo = selectObj.Geometry;
      geos.Add(geo);
      RhinoDoc.ActiveDoc.Objects.Delete(selectObj, true);
    }
    return geos;
  }

  private List<GeometryBase> Import3DM(string path)
  {
    RhinoDoc.ActiveDoc.Objects.UnselectAll();
    string cmd = "-_Import \"" + path + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    // check is selected objects are blocks
    var selectObjs = RhinoDoc.ActiveDoc.Objects.GetSelectedObjects(false, false).ToList();
    bool isBlock = false;

    foreach (var selectObj in selectObjs)
    {
      if (selectObj.ObjectType == Rhino.DocObjects.ObjectType.InstanceReference)
      {
        // if the selected object is a block, explode it
        isBlock = true;
        break;
      }
    }

    if (isBlock)
    {
      cmd = "-_ExplodeBlock _Enter";
      Rhino.RhinoApp.RunScript(cmd, false);
    }

    cmd = "-_Group _Enter _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    // get the selected objects
    selectObjs = RhinoDoc.ActiveDoc.Objects.GetSelectedObjects(false, false).ToList();
    List<GeometryBase> geos = new List<GeometryBase>();
    foreach (var selectObj in selectObjs)
    {
      GeometryBase geo = selectObj.Geometry;
      geos.Add(geo);
      RhinoDoc.ActiveDoc.Objects.Delete(selectObj, true);
    }
    return geos;
  }

  public void ChangeInputToggle(string targetInputName, bool state)
  {
    List<IGH_Param> inputs = Component.Params.Input;
    foreach (IGH_Param input in inputs)
    {
      if (input.Name != targetInputName) continue;
      IList<IGH_Param> sources = input.Sources;
      foreach (IGH_Param source in sources)
      {
        IGH_Attributes attributes = source.Attributes;
        IGH_DocumentObject comp_obj = attributes.GetTopLevel.DocObject;
        if (comp_obj.GetType() == typeof(Grasshopper.Kernel.Special.GH_BooleanToggle))
        {
          var toggle = source as Grasshopper.Kernel.Special.GH_BooleanToggle;
          if (toggle == null) continue;
          if (toggle.Value == state) continue;
          toggle.Value = state;
          comp_obj.ExpireSolution(true);
        }
      }
    }
  }
  #endregion
}