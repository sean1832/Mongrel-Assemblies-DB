using System;
using System.Collections;
using System.Collections.Generic;

using Rhino;
using Rhino.Geometry;

using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;

using System.IO;


/// <summary>
/// This class will be instantiated on demand by the Script component.
/// </summary>
public abstract class Script_Instance_90513 : GH_ScriptInstance
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
  private void RunScript(string csv, string col_pat, ref object data)
  {
    List<string> datas = SearchCsvColumn(csv, col_pat);
    data = datas;
  }
  #endregion
  #region Additional
  private List<string> SearchCsvColumn(string filePath, string pattern)
  {
    var matchedValues = new List<string>();

    if (!File.Exists(filePath))
    {
      Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "File not found");
      return null;
    }

    try
    {
      using (var reader = new StreamReader(filePath))
      {
        int lineCount = 0;
        int colIndex = -1;
        while (!reader.EndOfStream)
        {
          var line = reader.ReadLine();
          var values = line.Split(',');
          if (lineCount == 0)
          {
            for (var i = 0; i < values.Length; i++)
            {
              var value = values[i];
              if (value.StartsWith(pattern))
              {
                colIndex = i;
              }
            }
          }
          else
          {
            if (colIndex == -1)
            {
              Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Column not found");
              return null;
            }
            for (int i = 0; i < values.Length; i++)
            {
              if (i == colIndex)
              {
                var value = values[i];
                matchedValues.Add(value);
              }
            }
          }
          lineCount++;
        }
      }
    }
    catch (Exception e)
    {
      Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, e.Message);
      throw;
    }
    

    return matchedValues;
  }
  #endregion
}