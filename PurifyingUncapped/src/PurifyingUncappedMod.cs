namespace PurifyingUncapped
{
    /// <summary>
    /// Minimal IMod entry point. The loader applies [HarmonyPatch] classes itself
    /// (ModLoader.LoadModDll calls harmony.PatchAll(assembly)), so this class only
    /// needs to exist and log.
    /// </summary>
    public sealed class PurifyingUncappedMod : IMod
    {
        internal static ModLog Log;

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            Log.Log("Initialized: Purifying per-night removal cap 95% -> 100%");
        }

        public void OnEnable()
        {
        }

        public void OnDisable()
        {
        }
    }
}
