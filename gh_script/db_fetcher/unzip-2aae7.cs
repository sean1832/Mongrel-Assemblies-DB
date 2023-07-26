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
using System.IO.Compression;


/// <summary>
/// This class will be instantiated on demand by the Script component.
/// </summary>
public abstract class Script_Instance_2aae7 : GH_ScriptInstance
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
  private void RunScript(List<string> paths, bool run, ref object unziped)
  {
    if (run)
    {
      _files.Clear();
      string unzipPath = Path.GetDirectoryName(paths[0]) + "/unziped";

      // create a new folder
      Directory.CreateDirectory(unzipPath);
      int count = 0;
      foreach (var path in paths)
      {
        // check if the file is a gz file
        if (Path.GetExtension(path) == ".gz")
        {
          var decompressFile = DecompressFile(path, unzipPath);
          _files.Add(decompressFile);
          count++;
        }
        else
        {
          _files.Add(path);
        }
      }

      if (count == 0)
      {
        Component.Message = "No gz file found.\nYou can continue.";
      }
      else
      {
        Component.Message = "Done!\nUnzip " + count + " files";
      }
      
    }
    unziped = _files;
  }
  #endregion
  #region Additional
  private List<string> _files = new List<string>();

  private string DecompressFile(string path, string outDirectory)
  {
    var gzipFileName = Path.GetFileName(path); // Get the file name from the path (example.txt.gz)
    var originalFileName = Path.GetFileNameWithoutExtension(gzipFileName); // Remove the .gz extension (example.txt)

    var targetFilePath = Path.Combine(outDirectory, originalFileName); // Combine the output directory with the file name

    using (FileStream originalFileStream = File.OpenRead(path))
    {
      using (FileStream decompressedFileStream = File.Create(targetFilePath))
      {
        using (GZipStream decompressionStream = new GZipStream(originalFileStream, CompressionMode.Decompress))
        {
          decompressionStream.CopyTo(decompressedFileStream);
        }
      }
    }

    return targetFilePath;
  }
  #endregion
}