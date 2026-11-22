using System.Collections.Generic;

namespace FilterPrinterMod
{
    internal sealed class RetentionCategory
    {
        internal readonly string CaptionKey;
        internal readonly List<string> Liquids = new List<string>();

        internal RetentionCategory(string captionKey)
        {
            CaptionKey = captionKey;
        }
    }

    internal static class RetentionTargets
    {
        internal const string AllId = "all";

        private static readonly HashSet<string> Contaminants = new HashSet<string>
        {
            "microbe",
            "heavy_metal",
            "organic_waste",
            "mineral",
            "chemical_contaminant",
            "physical_contaminant",
            "microplastic",
            "plant_matter",
            "debris",
            "dream_cap_mush",
            "nightmare_cap_mush",
            "coffee_mush",
        };

        internal static readonly string[] ContaminantIds =
        {
            "microbe", "heavy_metal", "organic_waste", "mineral", "chemical_contaminant",
            "physical_contaminant", "microplastic", "plant_matter", "debris", AllId,
        };

        private static readonly string[] DrugIds =
        {
            "dream_cap_mush", "dream_cap_extract", "coffee_mush", "nightmare_extract",
            "nightmare_cap_mush", "alcohol", "caffeine", "fanta", "synaprest",
        };

        private static readonly string[] NutrientIds =
        {
            "protein", "fat", "starch", "sugar",
        };

        private static readonly string[] ChemicalIds =
        {
            "acid", "base", "chlorine", "zyanide", "reducing_agent", "stabilizing_agent",
            "methylol", "lipobond_agent", "contraceptive", "livestock_steroid",
            "livestock_immunity", "wine_extract", "nomore",
        };

        internal static readonly string[] CartridgeTargetIds = Combine(ContaminantIds, DrugIds, NutrientIds, ChemicalIds);

        internal static List<RetentionCategory> BuildCategories()
        {
            List<RetentionCategory> result = new List<RetentionCategory>();
            HashSet<string> known = new HashSet<string>();
            AddCategory(result, known, "tab.contaminants", ContaminantIds);
            AddCategory(result, known, "tab.drugs", DrugIds);
            AddCategory(result, known, "tab.nutrients", NutrientIds);
            AddCategory(result, known, "tab.chemicals", ChemicalIds);
            return result;
        }

        private static string[] Combine(params string[][] groups)
        {
            List<string> list = new List<string>();
            foreach (string[] group in groups)
            {
                list.AddRange(group);
            }
            return list.ToArray();
        }

        private static void AddCategory(List<RetentionCategory> result, HashSet<string> known, string captionKey, string[] ids)
        {
            RetentionCategory category = new RetentionCategory(captionKey);
            foreach (string id in ids)
            {
                if (id != AllId && !Liquid.LiquidDict.ContainsKey(id))
                {
                    continue;
                }
                if (known.Add(id))
                {
                    category.Liquids.Add(id);
                }
            }
            if (category.Liquids.Count > 0)
            {
                result.Add(category);
            }
        }

        internal static bool Blocks(string target, string liquidId)
        {
            if (string.IsNullOrEmpty(target) || string.IsNullOrEmpty(liquidId))
            {
                return false;
            }
            if (target == AllId)
            {
                return Contaminants.Contains(liquidId);
            }
            return string.Equals(target, liquidId);
        }

        internal static string DisplayName(string liquidId)
        {
            if (liquidId == AllId)
            {
                return Text.Get("target.all");
            }
            Liquid liquid;
            if (!string.IsNullOrEmpty(liquidId) && Liquid.LiquidDict.TryGetValue(liquidId, out liquid) && liquid != null && !string.IsNullOrEmpty(liquid.displayName))
            {
                return liquid.displayName;
            }
            return string.IsNullOrEmpty(liquidId) ? "?" : liquidId;
        }
    }
}
