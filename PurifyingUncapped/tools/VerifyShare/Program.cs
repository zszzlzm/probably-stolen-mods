using System;
using System.IO;
using System.Reflection;

// 离线核对 Prefix 的返回值，不启动游戏。
// 只做数值验证：直接反射调用 PurifyingSharePatch.Prefix，把结果和原版 PurifyingShare 对比。
// （不要在 .NET 8+ 上跑 Harmony 本身：游戏自带的 0Harmony 依赖 Mono 的 ILGenerator.MarkSequencePoint 重载。）
class Program
{
    const string Managed = @"F:\SteamLibrary\steamapps\common\Probably Stolen\Probably Stolen_Data\Managed";
    const string ModDll = @"F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped\PurifyingUncappedMod.dll";

    static int Main()
    {
        AppDomain.CurrentDomain.AssemblyResolve += (s, e) =>
        {
            string name = new AssemblyName(e.Name).Name + ".dll";
            string p = Path.Combine(Managed, name);
            return File.Exists(p) ? Assembly.LoadFrom(p) : null;
        };

        var asm = Assembly.LoadFrom(Path.Combine(Managed, "Assembly-CSharp.dll"));
        var t = asm.GetType("PlantWaterQuality", true);
        var original = t.GetMethod("PurifyingShare", BindingFlags.Public | BindingFlags.Static);

        var modAsm = Assembly.LoadFrom(ModDll);
        var patchType = modAsm.GetType("PurifyingUncapped.PurifyingSharePatch", true);
        var prefix = patchType.GetMethod("Prefix", BindingFlags.NonPublic | BindingFlags.Static)
                     ?? throw new Exception("Prefix not found");

        Console.WriteLine("rank | original | patched | tooltip");
        int failures = 0;
        foreach (int rank in new[] { 0, 5, 19, 20, 21, 22, 23, 25, 26, 30 })
        {
            float before = (float)original.Invoke(null, new object[] { rank });
            object[] args = { rank, 0f };
            prefix.Invoke(null, args);
            float after = (float)args[1];
            Console.WriteLine($"{rank,4} | {before,8:P2} | {after,8:P2} | {Math.Round(after * 100f)}%");

            float expected = rank <= 0 ? 0f : Math.Min(1f, 0.1f * (float)Math.Pow(rank, 0.75f));
            if (Math.Abs(after - expected) > 1e-5f) { failures++; Console.WriteLine($"  !! expected {expected}"); }
            if (rank <= 20 && Math.Abs(after - before) > 1e-6f) { failures++; Console.WriteLine("  !! rank<=20 must be unchanged"); }
            if (rank >= 22 && after < 0.99999f) { failures++; Console.WriteLine("  !! rank>=22 must be 100%"); }
        }
        Console.WriteLine(failures == 0 ? "OK: values match expectations" : $"FAILED: {failures} mismatch(es)");
        return failures == 0 ? 0 : 1;
    }
}
