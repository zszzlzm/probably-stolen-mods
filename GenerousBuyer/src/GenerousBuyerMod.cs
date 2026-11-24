using HarmonyLib;

namespace GenerousBuyer
{
    /// <summary>
    /// Minimal IMod entry point: the loader applies every [HarmonyPatch] class in this
    /// assembly itself (ModLoader.LoadModDll calls harmony.PatchAll(assembly)), so this class
    /// only needs to exist, hold the mod id and log.
    /// </summary>
    public sealed class GenerousBuyerMod : IMod
    {
        internal const string ModId = "harness.generous-buyer";

        internal static ModLog Log { get; private set; }

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            Log.Log("Initialized: Variety rule -> Generous (no duplicate restriction, +15% kept)");
        }

        public void OnEnable()
        {
            Log?.Log("Enabled");
        }

        public void OnDisable()
        {
            Log?.Log("Disabled (Harmony patches stay applied until the game restarts)");
        }
    }
}
