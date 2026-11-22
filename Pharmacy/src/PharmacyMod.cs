using System;

namespace PharmacyMod
{
    public sealed class PharmacyMod : IMod
    {
        internal const string ModId = "harness.district-pharmacy";

        private static ModLog log;
        private static bool hooksInstalled;
        private static bool debugRegistered;

        public void Init(ModManifest manifest)
        {
            log = new ModLog(manifest);
            ModHook.OnModItemDirectoryInit += OnItemDirectoryInit;
            log.Log("Initialized");
        }

        public void OnEnable()
        {
            if (!hooksInstalled)
            {
                hooksInstalled = true;
                ModHook.OnModAssetsLoaded += OnModAssetsLoaded;
                ModHook.OnGameLoadedInit += OnGameLoaded;
                ModHook.OnNewGameStarted += OnNewGameStarted;
            }
            log.Log("Enabled");
        }

        public void OnDisable()
        {
            ModHook.OnModItemDirectoryInit -= OnItemDirectoryInit;
            if (hooksInstalled)
            {
                hooksInstalled = false;
                ModHook.OnModAssetsLoaded -= OnModAssetsLoaded;
                ModHook.OnGameLoadedInit -= OnGameLoaded;
                ModHook.OnNewGameStarted -= OnNewGameStarted;
            }
            try
            {
                Recipes.Uninstall();
            }
            catch (Exception e)
            {
                log.Warning("Could not remove the recipes: " + e.Message);
            }
            ModHelper.RemoveDebugFunctions(ModId);
            debugRegistered = false;
        }

        private static void OnItemDirectoryInit(ModItemDirectory directory)
        {
            if (directory == null)
            {
                return;
            }
            directory.Add(Items.CalmAgentId, Items.CreateCalmAgent);
            directory.Add(Items.PainkillerId, Items.CreatePainkillerPill);
            log.Log("Registered 2 item ids");
        }

        private static void OnModAssetsLoaded(LoadedMod mod)
        {
            if (mod == null || mod.Manifest == null || mod.Manifest.ID != ModId)
            {
                return;
            }
            InstallRecipes("assets loaded");
            if (!debugRegistered)
            {
                debugRegistered = true;
                try
                {
                    ModHelper.AddDebugFunction(ModId, ModHelper.DEBUG_CATEGORY_SPAWN, Text.Get("debug.spawn_calm"),
                        () => Spawn(Items.CalmAgentId), true);
                    ModHelper.AddDebugFunction(ModId, ModHelper.DEBUG_CATEGORY_SPAWN, Text.Get("debug.spawn_pain"),
                        () => Spawn(Items.PainkillerId), true);
                }
                catch (Exception e)
                {
                    log.Warning("Could not add the debug buttons: " + e.Message);
                }
            }
        }

        private static void OnGameLoaded()
        {
            InstallRecipes("game loaded");
        }

        private static void OnNewGameStarted(string scenarioId)
        {
            InstallRecipes("new game");
        }

        private static void InstallRecipes(string reason)
        {
            try
            {
                int added = Recipes.Install();
                log.Log("Chem recipes installed (" + reason + "): +" + added + ", total " + Recipes.Total());
            }
            catch (Exception e)
            {
                log.Warning("Could not install the chem recipes (" + reason + "): " + e.GetType().Name + ": " + e.Message);
            }
        }

        private static void Spawn(string id)
        {
            GameItem item = ModHelper.SpawnItem(id);
            if (item == null)
            {
                log.Error("Could not create '" + id + "'");
                return;
            }
            ModHelper.MoveItemToInventory(ModHelper.SetItemOwnerShip(item, true));
        }

        internal static void LogInfo(string message)
        {
            if (log != null)
            {
                log.Log(message);
            }
        }
    }
}
