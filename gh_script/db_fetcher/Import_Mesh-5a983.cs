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
  private void RunScript(List<string> localPaths, bool import, ref object mesh)
  {

    if (import)
    {
      meshes.Clear();
      foreach (var path in localPaths)
      {
        var _geometries = ImportMesh(path);

        foreach (var geo in _geometries)
        {
          if (geo is Mesh)
          {
            meshes.Add(geo as Mesh);
          }
        }
      }
    }

    mesh = meshes;
    
  }
  #endregion
  #region Additional
  private List<Mesh> meshes = new List<Mesh>();

  private List<GeometryBase> ImportMesh(string path)
  {
    RhinoDoc.ActiveDoc.Objects.UnselectAll();
    string cmd = "-_Import \"" + path + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_SelAll \"" + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_Mesh \"" + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_SelMesh \"" + "\" _Enter";
    Rhino.RhinoApp.RunScript(cmd, false);

    cmd = "-_Join \"" + "\" _Enter";
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
  #endregion
}