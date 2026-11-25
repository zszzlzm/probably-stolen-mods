namespace ChemResale
{
    /// <summary>
    /// Minimal IMod entry point. The loader runs harmony.PatchAll on this assembly, so the
    /// [HarmonyPatch] classes in ChemResalePatches are installed without any code here.
    /// </summary>
    public sealed class ChemResaleMod : IMod
    {
        internal static ModLog Log;

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            Log.Log("Initialized: unpacked chemical reagents are priced at the water rate and typed CHEMICAL_SUPPLIES");
        }

        public void OnEnable()
        {
        }

        public void OnDisable()
        {
        }
    }
}
