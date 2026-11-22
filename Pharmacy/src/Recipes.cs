namespace PharmacyMod
{
    internal sealed class RecipeDef
    {
        internal readonly string Id;
        internal readonly string NameKey;
        internal readonly int Volume;
        internal readonly string IngredientId;

        internal RecipeDef(string id, string nameKey, int volume, string ingredientId)
        {
            Id = id;
            NameKey = nameKey;
            Volume = volume;
            IngredientId = ingredientId;
        }
    }

    /// <summary>
    /// 往化学精制机的配方表里加两条配方。界面每次打开都会重新读取这张表，
    /// 所以只要在本地化加载完成后追加即可，不需要 Harmony。
    /// </summary>
    internal static class Recipes
    {
        internal static readonly RecipeDef[] All =
        {
            new RecipeDef(Items.CalmAgentId, "item.calm_agent.name", Balance.CalmAgentVolume, "dream_cap_extract"),
            new RecipeDef(Items.PainkillerId, "item.painkiller_pill.name", Balance.PainkillerVolume, "fanta")
        };

        /// <summary>把缺失的配方加进去，返回新增条数。</summary>
        internal static int Install()
        {
            int added = 0;
            for (int i = 0; i < All.Length; i++)
            {
                RecipeDef def = All[i];
                ChemFinisherRecipe existing = ChemFinisherRecipe.GetRecipeById(def.Id);
                if (existing != null)
                {
                    // 已在表里（例如切换语言后重新执行），只刷新显示名
                    existing.displayName = Text.Get(def.NameKey);
                    continue;
                }
                ChemFinisherRecipe recipe = new ChemFinisherRecipe
                {
                    identifier = def.Id,
                    displayName = Text.Get(def.NameKey),
                    requiredVolume = def.Volume,
                    isRequireDry = Balance.RequireDry,
                    activeIngredientId = def.IngredientId
                };
                ChemFinisherRecipe.chemFinisherRecipes.Add(recipe);
                added++;
            }
            return added;
        }

        internal static void Uninstall()
        {
            for (int i = 0; i < All.Length; i++)
            {
                string id = All[i].Id;
                ChemFinisherRecipe.chemFinisherRecipes.RemoveAll((ChemFinisherRecipe recipe) => recipe.identifier == id);
            }
        }

        internal static int Total()
        {
            return ChemFinisherRecipe.chemFinisherRecipes.Count;
        }
    }
}
