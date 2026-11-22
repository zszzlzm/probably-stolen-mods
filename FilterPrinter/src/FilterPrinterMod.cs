using System;
using UnityEngine;

namespace FilterPrinterMod
{
    public sealed class FilterPrinterMod : IMod
    {
        internal const string ModId = "harness.filter-printer";
        internal const string UpgradeId = "harness.filter_printer.unlock";

        private static ModLog log;
        private static ConfigEntry<int> printPower;
        private static bool upgradeRegistered;
        private static bool hooksInstalled;
        private static bool debugRegistered;

        internal static int PrintPowerCost
        {
            get
            {
                int value = printPower != null ? printPower.Value : Balance.PrintPowerCost;
                if (value < 0)
                {
                    return 0;
                }
                if (value > 100000)
                {
                    return 100000;
                }
                return value;
            }
        }

        internal static void LogInfo(string message)
        {
            if (log != null)
            {
                log.Log(message);
            }
        }

        public void Init(ModManifest manifest)
        {
            log = new ModLog(manifest);
            ModHook.OnModItemDirectoryInit += OnItemDirectoryInit;
            ModHook.OnCreateTooltipLate += Tooltips.OnTooltip;
            try
            {
                printPower = ModHelper.GetConfig(manifest.ID).Define(
                    "print_power",
                    Balance.PrintPowerCost,
                    "Filter Printer",
                    () => Text.Get("config.power", printPower != null ? printPower.Value : Balance.PrintPowerCost),
                    tooltip: () => Text.Get("config.power_help"));
            }
            catch (Exception e)
            {
                log.Warning("Could not define the power setting: " + e.Message);
            }
            log.Log("Initialized");
        }

        public void OnEnable()
        {
            if (!hooksInstalled)
            {
                hooksInstalled = true;
                ModHook.OnGameLoadedInit += EnsureUpgrade;
                ModHook.OnNewGameStarted += OnNewGameStarted;
                ModHook.OnModAssetsLoaded += OnModAssetsLoaded;
            }
            log.Log("Enabled. Printer item registered: " + DirectoryMaster.Has<GameItem>(FilterPrinterMachine.ItemId));
        }

        public void OnDisable()
        {
            ModHook.OnModItemDirectoryInit -= OnItemDirectoryInit;
            ModHook.OnCreateTooltipLate -= Tooltips.OnTooltip;
            if (hooksInstalled)
            {
                hooksInstalled = false;
                ModHook.OnGameLoadedInit -= EnsureUpgrade;
                ModHook.OnNewGameStarted -= OnNewGameStarted;
                ModHook.OnModAssetsLoaded -= OnModAssetsLoaded;
            }
            ModHelper.RemoveNetworkUpgrades(ModId);
            ModHelper.RemoveDebugFunctions(ModId);
            upgradeRegistered = false;
            debugRegistered = false;
        }

        private static void OnModAssetsLoaded(LoadedMod mod)
        {
            if (mod == null || mod.Manifest == null || mod.Manifest.ID != ModId || debugRegistered)
            {
                return;
            }
            debugRegistered = true;
            try
            {
                ModHelper.AddDebugFunction(ModId, ModHelper.DEBUG_CATEGORY_SPAWN, Text.Get("debug.spawn"), SpawnPrinter, true);
            }
            catch (Exception e)
            {
                log.Warning("Could not add the debug button: " + e.Message);
            }
        }

        private static void OnNewGameStarted(string scenarioId)
        {
            EnsureUpgrade();
        }

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
                    Balance.UpgradeCost,
                    Text.Get("upgrade.subtitle"),
                    () => Text.Get("upgrade.title"),
                    () => Text.Get("upgrade.desc"),
                    GrantPrinter);
                upgradeRegistered = true;
                log.Log("Network upgrade registered");
            }
            catch (Exception e)
            {
                log.Warning("Could not register the network upgrade: " + e.Message);
            }
        }

        private static void OnItemDirectoryInit(ModItemDirectory directory)
        {
            if (directory == null)
            {
                return;
            }
            directory.Add(FilterPrinterMachine.ItemId, () => FilterPrinterMachine.Create());
            for (int i = 0; i < RetentionTargets.CartridgeTargetIds.Length; i++)
            {
                string target = RetentionTargets.CartridgeTargetIds[i];
                directory.Add(Cartridges.ItemId(target), () => Cartridges.Create(target));
            }
            log.Log("Registered " + (RetentionTargets.CartridgeTargetIds.Length + 1) + " item ids");
        }

        private static void GrantPrinter()
        {
            GameItem item = ModHelper.SpawnItem(FilterPrinterMachine.ItemId);
            if (item == null)
            {
                log.Error("Could not create the printer item");
                return;
            }
            ModHelper.MoveItemToBackCounter(ModHelper.SetItemOwnerShip(item, true));
        }

        private static void SpawnPrinter()
        {
            GameItem item = ModHelper.SpawnItem(FilterPrinterMachine.ItemId);
            if (item != null)
            {
                ModHelper.MoveItemToInventory(ModHelper.SetItemOwnerShip(item, true));
            }
        }
    }
}
