using System;
using System.Collections.Generic;
using UnityEngine;

namespace ReductionFernMod
{
    public sealed class ReductionFernMod : IMod
    {
        internal const string ModId = "harness.reduction-fern";
        internal const string SeedId = "restoring_fern_seed";
        internal const string ProduceId = "restoring_fern";
        internal const string UpgradeId = "harness.reduction_fern.unlock";
        internal const int UpgradeCost = 450;
        private const int SporesPerUnlock = 2;

        internal static ModLog Log { get; private set; }

        private static bool hooksInstalled;
        private static bool debugRegistered;
        private static bool upgradeRegistered;
        private static readonly List<(ModItemDirectory directory, string id)> registered =
            new List<(ModItemDirectory, string)>();

        public void Init(ModManifest manifest)
        {
            Log = new ModLog(manifest);
            ModHook.OnModItemDirectoryInit += OnItemDirectoryInit;
            ModHook.OnModAssetsLoaded += OnModAssetsLoaded;
            try
            {
                FernTraits.Register();
                FernPlant.Register();
            }
            catch (Exception e)
            {
                Log.Error("Could not register the plant or its trait: " + e);
            }
            HydroponicPlantArt.Install();
            SeedPreviewCompat.Install();
            Log.Log("Initialized");
        }

        public void OnEnable()
        {
            if (!hooksInstalled)
            {
                hooksInstalled = true;
                ModHook.OnGameLoadedInit += EnsureItemDirectories;
                ModHook.OnGameLoadedInit += EnsureUpgrade;
                ModHook.OnNewGameStarted += OnNewGameStarted;
            }
            EnsureItemDirectories();
            Log.Log("Enabled. Seed registered: " + DirectoryMaster.Has<GameItem>(SeedId)
                + ", fronds registered: " + DirectoryMaster.Has<GameItem>(ProduceId));
        }

        public void OnDisable()
        {
            ModHook.OnModItemDirectoryInit -= OnItemDirectoryInit;
            ModHook.OnModAssetsLoaded -= OnModAssetsLoaded;
            if (hooksInstalled)
            {
                hooksInstalled = false;
                ModHook.OnGameLoadedInit -= EnsureItemDirectories;
                ModHook.OnGameLoadedInit -= EnsureUpgrade;
                ModHook.OnNewGameStarted -= OnNewGameStarted;
            }
            UnregisterItems();
            HydroponicPlantArt.Uninstall();
            SeedPreviewCompat.Uninstall();
            FernPlant.Unregister();
            FernTraits.Unregister();
            ModHelper.RemoveNetworkUpgrades(ModId);
            upgradeRegistered = false;
            ModHelper.RemoveDebugFunctions(ModId);
            debugRegistered = false;
            Log.Log("Disabled");
        }

        private static void OnNewGameStarted(string scenarioId)
        {
            EnsureItemDirectories();
            EnsureUpgrade();
        }

        /// <summary>
        /// The network offer lives in the save's upgrade dictionary, so it has to be (re)registered
        /// after every load; RegisterModUpgrade is idempotent by id (NetworkUpgrade.cs:267-289).
        /// </summary>
        private static void EnsureUpgrade()
        {
            if (upgradeRegistered)
            {
                return;
            }
            try
            {
                ModHelper.AddNetworkUpgrade(
                    ModId,
                    UpgradeId,
                    UpgradeCost,
                    Text.Get("upgrade.subtitle"),
                    title: () => Text.Get("upgrade.title"),
                    description: () => Text.Get("upgrade.desc"),
                    onUnlock: GrantSpores,
                    iconKey: ModId + ":" + SeedId);
                upgradeRegistered = true;
                Log.Log("Network upgrade registered: " + UpgradeId + " (" + UpgradeCost + " cr, "
                    + SporesPerUnlock + " spores)");
            }
            catch (Exception e)
            {
                Log.Warning("Could not register the network upgrade: " + e.Message);
            }
        }

        private static void GrantSpores()
        {
            int given = 0;
            for (int i = 0; i < SporesPerUnlock; i++)
            {
                GameItem item = ModHelper.SpawnItem(SeedId);
                if (item == null)
                {
                    continue;
                }
                ModHelper.MoveItemToInventory(ModHelper.SetItemOwnerShip(item, true));
                given++;
            }
            Log.Log("Unlocked through the network; granted " + given + " spore(s)");
        }

        private static void EnsureItemDirectories()
        {
            // The preview mod's assembly may finish loading after our Init; retry the shim.
            SeedPreviewCompat.Install();
            ModItemDirectory[] directories = Resources.FindObjectsOfTypeAll<ModItemDirectory>();
            for (int i = 0; i < directories.Length; i++)
            {
                RegisterItems(directories[i]);
            }
        }

        private static void OnItemDirectoryInit(ModItemDirectory directory)
        {
            RegisterItems(directory);
        }

        private static void RegisterItems(ModItemDirectory directory)
        {
            if (directory == null)
            {
                return;
            }
            AddItem(directory, SeedId, FernItems.CreateSeed);
            AddItem(directory, ProduceId, FernItems.CreateNormal);
        }

        private static void AddItem(ModItemDirectory directory, string id, Func<GameItem> factory)
        {
            for (int i = 0; i < registered.Count; i++)
            {
                if (registered[i].directory == directory && registered[i].id == id)
                {
                    return;
                }
            }
            if (DirectoryMaster.Has<GameItem>(id))
            {
                Log.Warning("Item id '" + id + "' is already registered by someone else; not touching it.");
                return;
            }
            if (directory.Add(id, factory))
            {
                registered.Add((directory, id));
                Log.Log("Registered item id: " + id);
            }
            else
            {
                Log.Warning("Could not register item id: " + id);
            }
        }

        private static void UnregisterItems()
        {
            for (int i = 0; i < registered.Count; i++)
            {
                ModItemDirectory directory = registered[i].directory;
                if (directory != null && directory.Has(registered[i].id))
                {
                    directory.Remove(registered[i].id);
                }
            }
            registered.Clear();
        }

        private static void OnModAssetsLoaded(LoadedMod mod)
        {
            if (mod == null || mod.Manifest == null || mod.Manifest.ID != ModId)
            {
                return;
            }
            FernPlant.RefreshName();
            // Sprites only exist once the asset bundle is loaded; forget any earlier negative lookups.
            HydroponicPlantArt.ClearCache();
            // Another mod's assembly may only be loadable now; retry the preview shim (no-op once installed).
            SeedPreviewCompat.Install();
            if (debugRegistered)
            {
                return;
            }
            debugRegistered = true;
            try
            {
                ModHelper.AddDebugFunction(ModId, ModHelper.DEBUG_CATEGORY_SPAWN, Text.Get("debug.spawn"), SpawnSeed, true);
            }
            catch (Exception e)
            {
                Log.Warning("Could not add the debug button: " + e.Message);
            }
        }

        private static void SpawnSeed()
        {
            GameItem item = ModHelper.SpawnItem(SeedId);
            if (item != null)
            {
                ModHelper.MoveItemToInventory(ModHelper.SetItemOwnerShip(item, true));
            }
        }
    }
}
