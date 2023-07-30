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
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Security.Policy;


/// <summary>
/// This class will be instantiated on demand by the Script component.
/// </summary>
public abstract class Script_Instance_82ec0 : GH_ScriptInstance
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
  private void RunScript(List<string> hashes, List<string> urls, string tempDir, bool fetch, ref object localPaths, ref object loc_hash)
  {
    string unzipedDir = tempDir + "/unziped";
    if (fetch)
    {
      countExisting = 0;
      isRuned = true;
      msg = new List<string>();
      files = new List<string>();
      localHashes = new List<string>();
      try
      {
        WebClient client = new WebClient();
        if (!Directory.Exists(tempDir))
        {
          Directory.CreateDirectory(tempDir);
        }

        foreach (var url in urls)
        {
          string filename = url.Split('/')[url.Split('/').Length - 1];
          // get original file name
          string originalFilename = Path.GetFileNameWithoutExtension(filename);
          if (File.Exists(unzipedDir + "/" + originalFilename))
          {
            string existingHash = GetFileMd5Hash(unzipedDir + "/" + originalFilename);
            if (!hashes.Contains(existingHash)) // Check if the file's hash is not in the list of hashes
            {
              countExisting += 1;
              client.DownloadFile(new Uri(url), tempDir + "/" + filename);
              
              localHashes.Add(existingHash);
            }
          }
          else
          {
            countExisting += 1;
            client.DownloadFile(new Uri(url), tempDir + "/" + filename);
          }
          files.Add(tempDir + "/" + filename);
        }

      }
      catch (Exception e)
      {
        msg.Add(e.Message);
        errorInPreviousRun = true;
      }
    }

    if (files.Count > 0)
    {
      localPaths = files;
      loc_hash = localHashes;
    }


    if (errorInPreviousRun)
    {
      Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Error, string.Join("\n", msg));
    }
    else if (isRuned)
    {
      Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, "File downloaded at: " + tempDir);
      Component.Message = "Downloaded " + countExisting;
    }

  }
  #endregion
  #region Additional

  private int countExisting;
  private List<string> localHashes;
  List<string> msg;
  private bool errorInPreviousRun = false;
  private bool isRuned = false;
  private List<string> files;

  public static string GetFileMd5Hash(string filePath)
  {
    using (var md5 = MD5.Create())
    {
      using (var stream = File.OpenRead(filePath))
      {
        var hash = md5.ComputeHash(stream);
        return ByteArrayToString(hash);
      }
    }
  }

  private static string ByteArrayToString(byte[] ba)
  {
    StringBuilder hex = new StringBuilder(ba.Length * 2);
    foreach (byte b in ba)
      hex.AppendFormat("{0:x2}", b);
    return hex.ToString();
  }
  #endregion
}