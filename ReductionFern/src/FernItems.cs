using UnityEngine;

namespace ReductionFernMod
{
    /// <summary>
    /// Item factories. One item id for all three frond sizes (like dream_cap); the size is
    /// carried by the sprite key, which also decides the display name on reload.
    /// </summary>
    internal static class FernItems
    {
        internal const long SeedValue = 28;
        internal const float ReducingAgentPerGram = 0.25f;
        internal const float ValuePerGram = 0.45f;
        internal const float CaloriesPerGram = 1.2f;

        internal const string SeedSprite = "restoring_fern_seed";
        internal const string SmallSprite = "restoring_fern_s";
        internal const string NormalSprite = "restoring_fern";
        internal const string LargeSprite = "restoring_fern_l";

        internal static GameItem CreateSeed()
        {
            GameItem item = ItemDirectory.CreateEmptyItem(ReductionFernMod.SeedId);
            item.SetValue(SeedValue);
            item.SetGameItemType("SEED");
            item.SetSpriteAndShapeFromMod(ReductionFernMod.ModId, SeedSprite);
            item.SetShape(new GridShapeBuilder(1, 1).SetDataFill(1, 1, 1).Build());
            HydroponicHelper.InitSeedItem(item, ReductionFernMod.SeedId);
            // DirectoryMaster.Item() marks items owned, but our factories build from CreateEmptyItem();
            // without the tag every seed reads "(not owned)" in the tooltip and cannot be sold.
            GeneralHelper.SetItemOwned(item);
            ModHelper.SetSource(item, ReductionFernMod.ModId, Text.Get("mod.name"));
            item.onLoaded += LoadedSeed;
            LoadedSeed(item);
            return item;
        }

        internal static GameItem CreateSmall()
        {
            return CreateFronds(20.5f, SmallSprite);
        }

        internal static GameItem CreateNormal()
        {
            return CreateFronds(40f, NormalSprite);
        }

        internal static GameItem CreateLarge()
        {
            return CreateFronds(75f, LargeSprite);
        }

        private static GameItem CreateFronds(float weightGrams, string sprite)
        {
            GameItem item = ItemDirectory.CreateEmptyItem(ReductionFernMod.ProduceId);
            item.SetValue(Mathf.RoundToInt(ValuePerGram * weightGrams));
            item.SetGameItemType("CHEMICAL_SUPPLIES");
            // It is a crafting input first: MATERIAL puts it in the material category and lets furnaces accept it.
            item.SetGameItemType("MATERIAL");
            item.SetSpriteAndShapeFromMod(ReductionFernMod.ModId, sprite);
            item.SetShape(ShapeOf(sprite));
            ApplyComposition(item, weightGrams);
            AudioHelper.InitLeafy(item);
            // Per-item trait bonus (+5 ml reducing agent at rank I); must run after the base composition.
            PlantGeneticsHelper.ApplyFactoryGenetics(item, ReductionFernMod.SeedId);
            GeneralHelper.SetItemOwned(item);
            ModHelper.SetSource(item, ReductionFernMod.ModId, Text.Get("mod.name"));
            item.onLoaded += LoadedFronds;
            LoadedFronds(item);
            return item;
        }

        /// <summary>The three sprites are 1x1, 1x2 and 2x2 cells; set the footprint explicitly as well.</summary>
        private static GridShape ShapeOf(string sprite)
        {
            int width;
            int height;
            if (sprite == LargeSprite)
            {
                width = 2;
                height = 2;
            }
            else if (sprite == NormalSprite)
            {
                width = 1;
                height = 2;
            }
            else
            {
                width = 1;
                height = 1;
            }
            return new GridShapeBuilder(width, height).SetDataFill(width, height, 1).Build();
        }

        private static void ApplyComposition(GameItem item, float weightGrams)
        {
            ChemicalHelper.InitChemItem(item, isBlendable: true);
            // Vanilla produce always carries a calorie value even when it is not FOOD yet
            // (SetDreamCapComposition does the same). A spliced "edible" gene turns the item into
            // FOOD and sets its own 100 kcal, but this keeps the value sane for any other path and
            // for LoadEdibleProduce on reload.
            FoodItemHelper.InitFoodItem(item, Mathf.RoundToInt(CaloriesPerGram * weightGrams), isCanned: false);
            ChemicalHelper.SetChemContentML(item, FernTraits.LiquidId, ReducingAgentPerGram * weightGrams);
            ChemicalHelper.SetChemContentML(item, "water", 0.35f * weightGrams);
            ChemicalHelper.SetChemContentML(item, "plant_matter", 0.25f * weightGrams);
            ChemicalHelper.SetChemContentML(item, "protein", 0.05f * weightGrams);
            ChemicalHelper.SetChemContentML(item, "mineral", 0.0125f * weightGrams);
            ChemicalHelper.SetChemContentML(item, "physical_contaminant", 0.0375f * weightGrams);
            ChemicalHelper.SetChemContentML(item, "microbe", 0.025f * weightGrams);
        }

        private static void LoadedSeed(GameItem item)
        {
            // Repairs saves made before the factories set IS_OWNED_TAG.
            GeneralHelper.SetItemOwned(item);
            item.SetName(Text.Get("item.seed.name"));
            item.shortDescription = Text.Get("item.seed.desc");
            item.flavorText = Text.Get("item.seed.flavor");
        }

        private static void LoadedFronds(GameItem item)
        {
            // An "edible" gene splices onto the seed and MakeEdible() turns each harvested frond into
            // FOOD in place. Re-assert that on load so an old save keeps the FOOD type and calories
            // even if the game's own load pass ran in a different order.
            if (item.IsTag(PlantTraitList.EDIBLE_PRODUCE_TAG))
            {
                PlantTraitList.LoadEdibleProduce(item);
            }
            // Repairs saves made before the factories set IS_OWNED_TAG.
            GeneralHelper.SetItemOwned(item);
            string name = Text.Get("item.fronds.name");
            if (item.spritePath == SmallSprite)
            {
                name = LocHelper.GetLocalizedMechanic("item_size_small_of", name);
            }
            else if (item.spritePath == LargeSprite)
            {
                name = LocHelper.GetLocalizedMechanic("item_size_large_of", name);
            }
            item.SetName(name);
            item.shortDescription = Text.Get("item.fronds.desc");
            item.flavorText = Text.Get("item.fronds.flavor");
        }
    }
}
