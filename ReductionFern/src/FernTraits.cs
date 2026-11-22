using UnityEngine;

namespace ReductionFernMod
{
    /// <summary>
    /// The "produces reducing agent" trait. Mirrors the vanilla production traits
    /// (PlantTraitList.Production, private) line for line, including the harvest hook
    /// and the localization-template text, but with our own liquid and amount.
    /// </summary>
    internal static class FernTraits
    {
        internal const string LiquidId = "reducing_agent";
        internal const string ProductionId = PlantTraitList.PRODUCTION_PREFIX + LiquidId;
        internal const float MlAtRankOne = 5f;

        internal static PlantTrait Production { get; private set; }

        internal static void Register()
        {
            if (PlantTraitRegistry.Contains(ProductionId))
            {
                Production = PlantTraitRegistry.Get(ProductionId);
                ReductionFernMod.Log.Warning("Trait '" + ProductionId + "' is already registered; keeping the existing trait.");
                return;
            }

            Production = new PlantTrait(ProductionId, "Reducing Agent Production", 3)
                .Named(() => PlantGeneticsText.ProductionName(LiquidName()),
                       () => PlantGeneticsText.ProductionDescription(LiquidName()))
                .Infuses(LiquidId)
                .Unlimited()
                .AppliesToSeedProduce()
                .OnHarvestItem(Infuse)
                .Describe(rank => PlantGeneticsText.EffectProduction(Ml(rank).ToString("0.#"), LiquidName()));
            PlantTraitRegistry.Add(Production);
            MovePotencyTraitsLast();
        }

        internal static void Unregister()
        {
            if (Production != null && PlantTraitRegistry.Get(ProductionId) == Production)
            {
                PlantTraitRegistry.Remove(ProductionId);
            }
            Production = null;
        }

        internal static float Ml(int rank)
        {
            return MlAtRankOne * PlantGeneticsHelper.RankScale(rank);
        }

        private static void Infuse(PlantTraitContext context)
        {
            if (!context.item.IsTag(ChemicalHelper.CHEM_ITEM_TAG))
            {
                ChemicalHelper.InitChemItem(context.item, isBlendable: true);
            }
            ChemicalHelper.AddChemContentUL(context.item, LiquidId, Mathf.RoundToInt(Ml(context.rank) * 1000f));
        }

        private static string LiquidName()
        {
            Liquid liquid = Liquid.GetLiquidFromId(LiquidId);
            return liquid != null ? liquid.displayName : LiquidId;
        }

        /// <summary>
        /// Vanilla registers its production traits before potent/weak, so those two scale the
        /// trait bonus as well. A mod trait lands after them and would skip the multiplier;
        /// re-adding the same vanilla objects moves them to the end without redefining them.
        /// </summary>
        private static void MovePotencyTraitsLast()
        {
            PlantTrait potent = PlantTraitRegistry.Get(PlantTraitList.POTENT);
            if (potent != null)
            {
                PlantTraitRegistry.Add(potent);
            }
            PlantTrait weak = PlantTraitRegistry.Get(PlantTraitList.WEAK);
            if (weak != null)
            {
                PlantTraitRegistry.Add(weak);
            }
        }
    }
}
