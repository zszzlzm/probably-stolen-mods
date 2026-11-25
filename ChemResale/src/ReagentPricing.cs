using System.Collections.Generic;

namespace ChemResale
{
    /// <summary>
    /// Prototype A: give unpacked chemical reagents a price and a tradeable type.
    ///
    /// Vanilla state (0.46D):
    ///   * common/restricted chemical supply bags carry the CHEMICAL_SUPPLIES game item
    ///     type; the bottles they unpack into do not, so no chemical buyer matches them
    ///     (StoreClient.IsClientBuyingThisItem: blacklist -> ALL_TYPE -> id -> tag -> predicate).
    ///   * a filled reagent bottle keeps unitValue 3 (the empty bottle price from
    ///     FoodItemDirectory.MedBottleRed & co). The liquid is never priced: WaterHelper.AddLiquid
    ///     goes through WaterFeatureHelper.UpdateWaterFeature, which does not touch unitValue.
    ///   * every non-water liquid is graded as gutterflow water. GetPurityArrayIndex falls back
    ///     to 5 when no water purity bucket matches, and bucket 5 carries modValue -90, so a
    ///     reagent bottle sells for a tenth of its price and is labelled "unknown water (90%-)".
    ///     Vanilla never exposed that fallback because it had no sellable non-water container.
    ///
    /// This class applies the water rate (WaterFeatureHelper.GetWaterPrice, 40 per 1000 ml) to any
    /// container holding a reagent liquid, tags it CHEMICAL_SUPPLIES so the four vanilla chemical
    /// buyers can take it, and switches the water grading feature off.
    /// </summary>
    internal static class ReagentPricing
    {
        /// <summary>Liquids that make a container a reagent bottle. Contaminants are deliberately absent.</summary>
        private static readonly string[] Reagents =
        {
            "alcohol",
            "methylol",
            "reducing_agent",
            "acid",
            "base",
            "stabilizing_agent",
            "lipobond_agent",
            "chlorine",
        };

        internal const string SuppliesType = "CHEMICAL_SUPPLIES";

        /// <summary>Marker so the hot value path can recognise an already-normalised bottle without rescanning liquids.</summary>
        internal const string ReagentTag = "CHEM_RESALE_REAGENT_TAG";

        private const string WaterPurityCategory = "CATEGORY_WATER_PURITY";

        private static bool applying;

        internal static bool HasReagent(GameItem item)
        {
            if (item == null || !item.IsTag("LIQUID_CONTAINER_TAG"))
            {
                return false;
            }
            if (item.IsTag("WINE_CONTAINER_TAG"))
            {
                return false;
            }
            for (int i = 0; i < Reagents.Length; i++)
            {
                if (item.GetTagReadonly(Liquid.GetCurrentPartFromId(Reagents[i])).GetInt() > 0)
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// Cheap: no tag scan, no allocation. Called from the value read path, which runs for every
        /// tooltip/price lookup and must not rebuild volumes.
        /// </summary>
        internal static void SilenceWaterGrading(GameItem item)
        {
            if (item == null || !item.IsTag(ReagentTag))
            {
                return;
            }
            ItemFeature water = item.FindItemFeatureByCategory(WaterPurityCategory);
            if (water != null && !water.isDisabled)
            {
                water.isDisabled = true;
            }
        }

        /// <summary>Full normalisation. Idempotent, safe to call from any hook.</summary>
        internal static void Apply(GameItem item)
        {
            if (applying || item == null)
            {
                return;
            }
            applying = true;
            try
            {
                bool isReagent = HasReagent(item);
                if (!isReagent)
                {
                    // Poured the reagent out and refilled with water/anything else: give the
                    // container back to the vanilla grading instead of leaving a stale marker.
                    if (item.IsTag(ReagentTag))
                    {
                        item.DisableTag(ReagentTag);
                    }
                    return;
                }

                int total = WaterHelper.GetTotalVolume(item);
                long price = WaterFeatureHelper.GetWaterPrice(total);

                bool repriced = item.unitValue != price;
                if (repriced)
                {
                    item.SetValue(price);
                }

                bool retagged = !item.IsGameItemType(SuppliesType);
                if (retagged)
                {
                    item.SetGameItemType(SuppliesType);
                }

                bool first = !item.IsTag(ReagentTag);
                if (first)
                {
                    item.EnableTag(ReagentTag);
                }

                SilenceWaterGrading(item);

                if (first || repriced || retagged)
                {
                    ChemResaleMod.Log?.Log(string.Format(
                        "reagent {0} ({1}): {2} ml -> unitValue {3}, supply type {4}, water grading off",
                        item.name, item.identifier, total / 1000, price, SuppliesType));
                }
            }
            finally
            {
                applying = false;
            }
        }
    }
}
