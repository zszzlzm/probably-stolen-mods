using HarmonyLib;
using UnityEngine;

namespace PurifyingUncapped
{
    /// <summary>
    /// Replaces PlantWaterQuality.PurifyingShare(int).
    ///
    /// Original:
    ///     return Mathf.Min(0.95f, 0.1f * PlantGeneticsHelper.RankScale(rank));
    ///
    /// Patched:
    ///     return Mathf.Min(1f, 0.1f * PlantGeneticsHelper.RankScale(rank));
    ///
    /// This is the ONLY place the 95% cap is applied. The method has exactly two
    /// call sites in Assembly-CSharp: PlantWaterQuality.Purify (actual removal) and
    /// PlantWaterQuality.DescribePurifying (tooltip text), so a prefix here updates
    /// both gameplay and UI consistently.
    /// </summary>
    [HarmonyPatch(typeof(PlantWaterQuality), nameof(PlantWaterQuality.PurifyingShare))]
    internal static class PurifyingSharePatch
    {
        private static bool Prefix(int rank, ref float __result)
        {
            if (rank <= 0)
            {
                __result = 0f;
                return false;
            }

            __result = Mathf.Min(1f, 0.1f * PlantGeneticsHelper.RankScale(rank));
            return false;
        }
    }
}
