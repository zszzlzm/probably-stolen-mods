namespace ReductionFernMod
{
    /// <summary>The plant definition and its harvest. Structure follows HarvestDreamCap.</summary>
    internal static class FernPlant
    {
        internal const int GrowthProgress = 26;
        internal const int HarvestQuantity = 8;

        internal static PlantDefinition Definition { get; private set; }

        internal static void Register()
        {
            if (PlantRegistry.Contains(ReductionFernMod.SeedId))
            {
                Definition = PlantRegistry.Get(ReductionFernMod.SeedId);
                ReductionFernMod.Log.Warning("Plant '" + ReductionFernMod.SeedId + "' is already registered; keeping the existing definition.");
                return;
            }

            Definition = PlantRegistry.Add(new PlantDefinition(
                    ReductionFernMod.SeedId,
                    "Reduction Fern",
                    ReductionFernMod.ProduceId,
                    GrowthProgress,
                    HarvestQuantity)
                .Nutriment(250, 75, 30)
                .Contaminant(1.01)
                .ReturnsSeeds()
                .Innate(PlantTraitList.DROUGHT_RESISTANT)
                .Innate(FernTraits.ProductionId)
                .OnHarvest(Harvest));
        }

        internal static void Unregister()
        {
            if (Definition != null && PlantRegistry.Get(ReductionFernMod.SeedId) == Definition)
            {
                PlantRegistry.Remove(ReductionFernMod.SeedId);
            }
            Definition = null;
        }

        /// <summary>Plant names are baked as strings, so they can only be localized once the mod assets are loaded.</summary>
        internal static void RefreshName()
        {
            if (Definition != null)
            {
                Definition.displayName = Text.Get("plant.name");
            }
        }

        private static void Harvest(PlantHarvestContext context)
        {
            PlantHarvest.SizeSplit split = PlantHarvest.SplitByHealth(
                context.harvestCount, context.health, reduceCount: true, allowHuge: false);

            context.OutputById(ReductionFernMod.SeedId);
            PlantHarvest.OutputSplit(context, split, FernItems.CreateSmall, FernItems.CreateNormal, FernItems.CreateLarge);
        }
    }
}
