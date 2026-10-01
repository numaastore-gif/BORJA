using System.Text;
using System.Text.Json;
using DotNetSiemensPLCToolBoxLibrary.Projectfiles;
using DotNetSiemensPLCToolBoxLibrary.DataTypes.Blocks;
using DotNetSiemensPLCToolBoxLibrary.DataTypes.Blocks.Step7V5;
using DotNetSiemensPLCToolBoxLibrary.DataTypes.Projectfolders.Step7V5;
using DotNetSiemensPLCToolBoxLibrary.DataTypes.AWL.Step7V5;
using DotNetSiemensPLCToolBoxLibrary.DataTypes;

Encoding.RegisterProvider(CodePagesEncodingProvider.Instance);
var prj = new Step7ProjectV5(args[0], false);
var outDir = args[1]; Directory.CreateDirectory(outDir);
var cpus = new List<object>();
foreach (var c in prj.CPUFolders) cpus.Add(new { c.Name, Type = c.CpuType.ToString(), c.MLFB_OrderNumber, c.Rack, c.Slot, Parent = c.Parent?.Name });
File.WriteAllText(Path.Combine(outDir,"cpus.json"), JsonSerializer.Serialize(cpus, new JsonSerializerOptions{WriteIndented=true}));

object DR(IDataRow r) {
  var s = r as S7DataRow;
  if (s==null) return new { Name = r.Name };
  string addr=""; try { addr = s.BlockAddress?.ToString() ?? ""; } catch {}
  string sv=""; try { sv = s.StartValueAsString; } catch {}
  string dt=""; try { dt = s.DataTypeAsString; } catch { dt = s.DataType.ToString(); }
  return new { s.Name, DataType = dt, Address = addr, s.Comment, StartValue = sv, Children = s.Children.Select(DR).ToList() };
}
int pi=0;
foreach (var p in prj.S7ProgrammFolders) {
  pi++;
  var o = new Dictionary<string, object?>();
  o["Name"] = p.Name; o["Parent"] = p.Parent?.Name; o["ParentParent"]=p.Parent?.Parent?.Name;
  o["BlocksFolder"] = p.BlocksOfflineFolder?.Folder;
  var st = p.SymbolTable as SymbolTable;
  o["SymbolFolder"] = st?.Folder;
  o["Symbols"] = st?.SymbolTableEntrys.Select(e => new { e.Symbol, e.Operand, e.OperandIEC, e.DataType, e.Comment }).ToList();
  var blocks = new List<object>();
  if (p.BlocksOfflineFolder != null) {
    var opt = new S7ConvertingOptions(MnemonicLanguage.German) { ReplaceDBAccessesWithSymbolNames=false, ReplaceLokalDataAddressesWithSymbolNames=true, ReplaceDIAccessesWithSymbolNames=true, CombineDBOpenAndDBAccess=true, GenerateCallsfromUCs=true, UseComments=true };
    foreach (var bi in p.BlocksOfflineFolder.readPlcBlocksList()) {
      var d = new Dictionary<string, object?>();
      d["Name"]=bi.Name; d["Type"]=bi.BlockType.ToString(); d["Lang"]=bi.BlockLanguage.ToString();
      try {
        var b = p.BlocksOfflineFolder.GetBlock(bi, opt);
        d["Name"]=b.BlockName; d["Symbol"] = b.SymbolTableEntry?.Symbol; d["SymComment"]=b.SymbolTableEntry?.Comment;
        if (b is S7Block sb) { d["Title"]=sb.Title; d["Author"]=sb.Author; d["Family"]=sb.Family; d["Version"]=sb.Version; d["LastCodeChange"]=sb.LastCodeChange.ToString("yyyy-MM-dd HH:mm"); d["Lang"]=sb.BlockLanguage.ToString(); d["KnowHow"]=sb.KnowHowProtection; d["CodeSize"]=sb.CodeSize; }
        if (b is S7FunctionBlock fb) {
          d["Description"]=fb.Description;
          try { d["Interface"] = fb.Parameter==null?null:DR(fb.Parameter); } catch (Exception ex) { d["InterfaceErr"]=ex.Message; }
          var nets = new List<object>(); int ni=0;
          foreach (var n in fb.Networks ?? new List<Network>()) {
            ni++;
            var rows = new List<object>();
            foreach (var r0 in n.AWLCode) {
              var r = r0 as S7FunctionBlockRow;
              if (r==null) continue;
              List<object>? cps=null;
              if (r.CallParameter!=null) cps = r.CallParameter.Select(cp => (object)new { cp.Name, Value=cp.Value, Dir=cp.ParameterType.ToString(), Type=cp.ParameterDataType.ToString() }).ToList();
              string pr=""; try { pr = r.Parameter; } catch {}
              string sym=""; try { sym = r.SymbolTableEntry?.Symbol ?? ""; } catch {}
              rows.Add(new { r.Label, r.Command, Parameter=pr, r.Comment, Sym=sym, Call=cps, Txt=r.ToString(false,false) });
            }
            nets.Add(new { N=ni, n.Name, n.Comment, Rows=rows });
          }
          d["Networks"]=nets;
        }
        if (b is S7DataBlock db) {
          d["IsInstance"]=db.IsInstanceDB; d["FB"]=db.FBNumber;
          try { d["Structure"]= db.Structure==null?null:DR(db.Structure); } catch (Exception ex) { d["StructErr"]=ex.Message; }
        }
      } catch (Exception ex) { d["Error"]=ex.GetType().Name+": "+ex.Message; }
      blocks.Add(d);
    }
  }
  o["Blocks"]=blocks;
  File.WriteAllText(Path.Combine(outDir,$"prog{pi}.json"), JsonSerializer.Serialize(o, new JsonSerializerOptions{WriteIndented=false, Encoder=System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping}));
  Console.WriteLine($"prog{pi}: {p.Name} parent={p.Parent?.Name} blocks={blocks.Count} folder={p.BlocksOfflineFolder?.Folder} sym={st?.Folder} nsym={st?.SymbolTableEntrys.Count}");
}
